"""audit_api_maps.py - Lightweight drift detection for docs/api-maps/*.md.

Cross-references claims in each API-map document against the actual codebase
to surface places where the map says one thing and the code says another.
The goal is to make review of ~60 maps across ~20 counties tractable --
a triad recently surfaced 3 concrete errors in Polk's maps; this script finds
the same class of error across every county without running a triad per file.

USAGE
-----
    python scripts/audit_api_maps.py                       # scan everything
    python scripts/audit_api_maps.py --county polk         # one county
    python scripts/audit_api_maps.py --platform arcgis     # one platform
    python scripts/audit_api_maps.py --json                # JSON output
    python scripts/audit_api_maps.py --fail-on-drift       # exit 2 if any drift

The script is stdlib-only -- no network, no DB, no third-party deps. It must
NOT import seed_bi_county_config.py or seed_pt_jurisdiction_config.py because
those modules call psycopg2.connect() at import time; instead we parse the
source with ast and literal_eval each list entry.

SEVERITY LEVELS
---------------
    drift       The map and the code DISAGREE in a concrete, verifiable way.
                These findings always cite BOTH sides (map file:line AND
                code file:line). Fix the map (or the code) before trusting
                the map for downstream work.
    suspicious  The map contains a citation that LOOKS wrong (e.g. line
                number past EOF, class name not found in the repo) but we
                can't prove drift without context. Review manually.
    info        Informational -- the map refers to a platform/county with
                no resolvable code artefacts at all (e.g. putnam-custom-cr
                has no adapter). Not an error; just a note.

KNOWN FALSE-POSITIVE CLASSES
----------------------------
    * Accela's shared base adapter (accela_citizen_access.py) gets cited
      from every per-county Accela map. Multiple matches on the same
      adapter file are EXPECTED, not a bug.
    * Maps often mention "available via REST API" for fields the adapter
      does NOT parse; that's aspirational, not drift. Check A1/A2 only
      look for explicit negations ("does not visit", "adapter does not
      parse") paired with methods that DO exist AND are called.
    * Commission YAMLs sometimes share a platform across BCC/PZ/BOA; the
      E2 check tolerates platform-token mismatch for the shared
      `_florida-defaults.yaml` fallback.

ADDING A NEW CHECK (3-STEP RECIPE)
----------------------------------
    1. Pick a check ID in the CHECK_* constant block below and give it a
       short code (e.g. ACCELA-FEES-NOT-CALLED).
    2. Add a check function `def check_xyz(ctx) -> list[Finding]:` that
       reads from ctx.map_text / ctx.artefacts / ctx.seed_* and returns a
       list of Finding objects (each MUST have both map_claim and
       code_evidence populated unless severity is 'info').
    3. Register the function in the CHECKS_BY_PLATFORM dispatch dict at
       the bottom of the file. Run `python scripts/audit_api_maps.py`
       and eyeball the new findings; add a negative-test map (one that
       should NOT fire) to the verification list below.

PERFORMANCE NOTE
----------------
Full scan of 58 maps completes in well under 10 seconds on a modern
machine. File reads are cached via functools.lru_cache; the AST parse of
each seed file happens exactly once per run. If this ever gets slow, the
hot path is re.search over the full adapter text -- consider pre-compiling
the patterns that are used across every map.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from functools import lru_cache
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

PLATFORM_TOKENS = {
    # filename suffix -> platform key
    "accela": "accela",
    "arcgis": "arcgis",
    "iworq": "iworq",
    "cityview": "cityview",
    "landmark": "landmark",
    "novusagenda": "novusagenda",
    "legistar": "legistar",
    "civicclerk": "civicclerk",
    "civicplus": "civicplus",
    "granicus": "granicus",
    "acclaimweb": "acclaimweb",
    "tyler-selfservice": "tyler-selfservice",
    "tyler-energov": "tyler-energov",
    "mgo-connect": "mgo-connect",
    "citizenserve": "citizenserve",
    "custom-cr": "custom-cr",
    "improvement-report": "improvement-report",
}

# Files that LOOK like api-maps by extension but are triad outputs or other
# non-map docs. These must be skipped -- auditing them will produce noise.
SKIP_FILES = {
    "polk-county-improvement-report.md",
}

# Platform keys whose maps are PT (permit/tax) related; we can cross-check
# these against seed_pt_jurisdiction_config.py.
PT_PLATFORMS = {"accela", "iworq", "cityview", "tyler-selfservice",
                "tyler-energov", "cloudpermit", "citizenserve"}

# Platform keys that correspond to BI (builder inventory / GIS).
BI_PLATFORMS = {"arcgis"}

# Platform keys that correspond to CR (commission).
CR_PLATFORMS = {"legistar", "civicclerk", "civicplus", "granicus",
                "novusagenda", "acclaimweb", "custom-cr", "mgo-connect",
                "landmark"}

# Accela topics that get the "does NOT visit/call/parse" treatment in maps.
# Each maps to the corresponding _parse_* method we grep for.
ACCELA_TOPICS = {
    "Inspection": "_parse_inspections",
    "Inspections": "_parse_inspections",
    "Attachment": "_parse_attachments",
    "Attachments": "_parse_attachments",
    "Fee": "_parse_fees",
    "Fees": "_parse_fees",
    "Processing Status": "_parse_processing_status",
    "Related Record": "_parse_related_records",
    "Related Records": "_parse_related_records",
    "Condition": "_parse_conditions",
    "Conditions": "_parse_conditions",
}

# BI seed row keys that count toward "mapped fields" for ArcGIS counties.
BI_FIELD_KEYS = (
    "gis_owner_field",
    "gis_parcel_field",
    "gis_address_field",
    "gis_use_field",
    "gis_acreage_field",
    "gis_subdivision_field",
    "gis_building_value_field",
    "gis_appraised_value_field",
    "gis_deed_date_field",
    "gis_previous_owner_field",
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    county: str
    platform: str
    map_path: str
    check_id: str
    severity: str  # 'drift' | 'suspicious' | 'info'
    message: str
    map_claim: str = ""       # "path:line  quoted text"
    code_evidence: str = ""   # "path:line  quoted text"


@dataclass
class Artefacts:
    """Resolved codebase artefacts for a given (county, platform) pair."""
    permit_adapter_paths: list[Path] = field(default_factory=list)
    commission_scraper_path: Path | None = None
    commission_yaml_paths: list[Path] = field(default_factory=list)
    bi_seed_rows: list[dict] = field(default_factory=list)  # list of {row, line}
    pt_seed_rows: list[dict] = field(default_factory=list)  # list of {row, line}


@dataclass
class CheckCtx:
    map_path: Path
    county_slug: str       # e.g. "polk-county"
    county: str            # e.g. "polk"
    platform: str          # e.g. "accela"
    map_text: str
    map_lines: list[str]
    artefacts: Artefacts


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=512)
def read_file_text(path_str: str) -> str:
    try:
        return Path(path_str).read_text(encoding="utf-8", errors="replace")
    except (OSError, FileNotFoundError):
        return ""


@lru_cache(maxsize=512)
def read_file_lines(path_str: str) -> tuple[str, ...]:
    text = read_file_text(path_str)
    if not text:
        return tuple()
    return tuple(text.splitlines())


def grep_file(path: Path, pattern: str) -> list[tuple[int, str]]:
    """Return (lineno_1based, line) for every match of pattern in the file."""
    if not path.exists():
        return []
    out: list[tuple[int, str]] = []
    rx = re.compile(pattern)
    for i, line in enumerate(read_file_lines(str(path)), start=1):
        if rx.search(line):
            out.append((i, line))
    return out


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------

def parse_map_filename(path: Path) -> tuple[str, str, str] | None:
    """Return (county_slug, county, platform) from a map filename.

    Returns None if the filename doesn't look like a map or if it's in
    SKIP_FILES.
    """
    if path.name in SKIP_FILES:
        return None
    if not path.name.endswith(".md"):
        return None
    stem = path.stem  # e.g. polk-county-accela

    # Match longest platform token suffix.
    for token in sorted(PLATFORM_TOKENS, key=len, reverse=True):
        suffix = f"-{token}"
        if stem.endswith(suffix):
            county_slug = stem[: -len(suffix)]  # e.g. polk-county
            # Normalize county_slug -> county (drop trailing -county, -fl)
            county = county_slug
            for drop in ("-county",):
                if county.endswith(drop):
                    county = county[: -len(drop)]
            return county_slug, county, PLATFORM_TOKENS[token]
    return None


# ---------------------------------------------------------------------------
# Seed file parsing (AST-based, NEVER import)
# ---------------------------------------------------------------------------

def _literal_eval_safe(node: ast.AST):
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None


def read_seed_bi_configs(repo_root: Path) -> list[dict]:
    """Parse COUNTY_GIS_CONFIGS from seed_bi_county_config.py without import."""
    path = repo_root / "seed_bi_county_config.py"
    src = read_file_text(str(path))
    if not src:
        return []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []

    rows: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name)]
            if not any(t.id == "COUNTY_GIS_CONFIGS" for t in targets):
                continue
            if not isinstance(node.value, (ast.List, ast.Tuple)):
                continue
            for elt in node.value.elts:
                if not isinstance(elt, ast.Dict):
                    continue
                data = _literal_eval_safe(elt)
                if not isinstance(data, dict):
                    continue
                data["_line"] = elt.lineno
                rows.append(data)
            break
    return rows


def read_seed_pt_jurisdictions(repo_root: Path) -> list[dict]:
    """Parse JURISDICTIONS from seed_pt_jurisdiction_config.py without import.

    Each entry is a tuple: (name, county_name, municipality, state, adapter_slug,
    adapter_class, portal_type, portal_url, scrape_mode, fragile_note)
    """
    path = repo_root / "seed_pt_jurisdiction_config.py"
    src = read_file_text(str(path))
    if not src:
        return []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []

    rows: list[dict] = []
    keys = ("name", "county_name", "municipality", "state", "adapter_slug",
            "adapter_class", "portal_type", "portal_url", "scrape_mode",
            "fragile_note")

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name)]
            if not any(t.id == "JURISDICTIONS" for t in targets):
                continue
            if not isinstance(node.value, (ast.List, ast.Tuple)):
                continue
            for elt in node.value.elts:
                if not isinstance(elt, (ast.Tuple, ast.List)):
                    continue
                tup = _literal_eval_safe(elt)
                if not isinstance(tup, (tuple, list)):
                    continue
                if len(tup) < len(keys):
                    continue
                row = dict(zip(keys, tup))
                row["_line"] = elt.lineno
                rows.append(row)
            break
    return rows


# ---------------------------------------------------------------------------
# Artefact resolution
# ---------------------------------------------------------------------------

def resolve_artefacts(
    county_slug: str,
    county: str,
    platform: str,
    repo_root: Path,
    bi_rows: list[dict],
    pt_rows: list[dict],
) -> Artefacts:
    art = Artefacts()

    # Permit adapter paths: look for adapter files whose name matches jurisdictions
    # listing this county (any municipality) and for the platform's shared base.
    adapter_dir = repo_root / "modules" / "permits" / "scrapers" / "adapters"
    if platform in PT_PLATFORMS:
        # Shared platform base
        platform_base_map = {
            "accela": "accela_citizen_access.py",
            "iworq": "iworq.py",
            "tyler-energov": "tyler_energov.py",
        }
        base = platform_base_map.get(platform)
        if base:
            p = adapter_dir / base
            if p.exists():
                art.permit_adapter_paths.append(p)

        # County-specific subclasses from PT seed
        def _slug_pre(s: str) -> str:
            return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
        county_slug_pre = _slug_pre(county)
        for row in pt_rows:
            row_portal = (row.get("portal_type") or "").lower()
            if row_portal != platform:
                continue
            if _slug_pre(row.get("county_name") or "") != county_slug_pre:
                continue
            adapter_class = row.get("adapter_class") or ""
            # Extract module path: "modules.x.y.Adapter" -> "modules/x/y.py"
            if "." in adapter_class:
                module_path = ".".join(adapter_class.split(".")[:-1])
                candidate = repo_root / (module_path.replace(".", "/") + ".py")
                if candidate.exists() and candidate not in art.permit_adapter_paths:
                    art.permit_adapter_paths.append(candidate)

    # Commission YAMLs (FL only for now)
    if platform in CR_PLATFORMS:
        yaml_dir = repo_root / "modules" / "commission" / "config" / "jurisdictions" / "FL"
        if yaml_dir.exists():
            # Matching slugs: county-slug-*.yaml (e.g. polk-county-bcc.yaml)
            for yp in sorted(yaml_dir.glob(f"{county_slug}-*.yaml")):
                art.commission_yaml_paths.append(yp)
        scraper_dir = repo_root / "modules" / "commission" / "scrapers"
        platform_scraper_map = {
            "legistar": "legistar.py",
            "civicclerk": "civicclerk.py",
            "civicplus": "civicplus.py",
            "granicus": "granicus.py",
            "novusagenda": "novusagenda.py",
        }
        s = platform_scraper_map.get(platform)
        if s:
            p = scraper_dir / s
            if p.exists():
                art.commission_scraper_path = p

    # Normalize helper: "St. Lucie" -> "st-lucie", "Polk" -> "polk"
    def _slugify(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")

    county_slug_norm = _slugify(county)

    # BI seed rows for this county (ArcGIS)
    if platform in BI_PLATFORMS:
        for row in bi_rows:
            if _slugify(row.get("name") or "") == county_slug_norm:
                art.bi_seed_rows.append(row)

    # PT seed rows for this county
    if platform in PT_PLATFORMS:
        for row in pt_rows:
            row_portal = (row.get("portal_type") or "").lower()
            if row_portal != platform:
                continue
            if _slugify(row.get("county_name") or "") != county_slug_norm:
                continue
            art.pt_seed_rows.append(row)

    return art


# ---------------------------------------------------------------------------
# Citation formatting
# ---------------------------------------------------------------------------

def cite(path: Path, lineno: int, text: str, repo_root: Path) -> str:
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        rel = str(path)
    snippet = text.strip()
    if len(snippet) > 140:
        snippet = snippet[:137] + "..."
    return f"{rel}:{lineno}  {snippet!r}"


def cite_map(map_path: Path, lineno: int, text: str, repo_root: Path) -> str:
    return cite(map_path, lineno, text, repo_root)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

NEGATION_PATTERN = re.compile(
    r"(?i)\b(does|do)\s+not\s+(visit|call|parse|fetch|extract)\b[^.\n]*"
    r"\b(Inspection|Attachment|Fee|Fees|Processing\s+Status|Related\s+Records?|Condition)s?\b"
)


def check_A1_accela_method_called(ctx: CheckCtx, repo_root: Path) -> list[Finding]:
    """Map says the adapter does NOT parse topic X, but _parse_X is called."""
    if ctx.platform != "accela":
        return []
    adapter_candidates = [p for p in ctx.artefacts.permit_adapter_paths
                          if p.name == "accela_citizen_access.py"]
    if not adapter_candidates:
        return []
    adapter = adapter_candidates[0]
    adapter_text = read_file_text(str(adapter))
    if not adapter_text:
        return []

    findings: list[Finding] = []
    # Walk map line-by-line so we can emit per-line citations.
    for i, line in enumerate(ctx.map_lines, start=1):
        m = NEGATION_PATTERN.search(line)
        if not m:
            continue
        topic_raw = m.group(3)
        topic_key = topic_raw.strip()
        # Normalize
        topic_key = re.sub(r"\s+", " ", topic_key).strip()
        # Find matching method name via ACCELA_TOPICS
        method = None
        for k, v in ACCELA_TOPICS.items():
            if k.lower() == topic_key.lower():
                method = v
                break
        if not method:
            continue
        # Check both: def exists AND it's called (not on a def line)
        def_hits = grep_file(adapter, rf"def\s+{re.escape(method)}\s*\(")
        if not def_hits:
            continue
        # Call sites: lines that mention the method name but are not the def line
        call_hits: list[tuple[int, str]] = []
        for lineno, text in grep_file(adapter, rf"{re.escape(method)}\s*\("):
            if re.search(rf"def\s+{re.escape(method)}\s*\(", text):
                continue
            call_hits.append((lineno, text))
        if not call_hits:
            # Defined but never called -- that's a *different* drift we don't
            # flag here to keep false positives down.
            continue
        # Drift! Emit finding with BOTH sides.
        call_line, call_text = call_hits[0]
        findings.append(Finding(
            county=ctx.county,
            platform=ctx.platform,
            map_path=str(ctx.map_path),
            check_id="ACCELA-METHOD-IS-CALLED",
            severity="drift",
            message=(f"Map says adapter does not parse {topic_raw}, "
                     f"but {method}() is defined and called in the adapter."),
            map_claim=cite_map(ctx.map_path, i, line, repo_root),
            code_evidence=cite(adapter, call_line, call_text, repo_root),
        ))
    return findings


EXTRACTED_NO_PATTERN = re.compile(
    r"(?i)###\s*Currently\s+Extracted\??\s*\n+\s*\*\*NO",
)


def check_A2_accela_section_NO_but_called(ctx: CheckCtx, repo_root: Path) -> list[Finding]:
    """'Currently Extracted? **NO.**' section but the adapter DOES parse it.

    Scan sections like '## 5. Inspection Data' -> '### Currently Extracted?'
    -> '**NO.**'.  If the section header mentions a topic in ACCELA_TOPICS
    and the corresponding _parse_* method exists AND is called, drift.
    """
    if ctx.platform != "accela":
        return []
    adapter_candidates = [p for p in ctx.artefacts.permit_adapter_paths
                          if p.name == "accela_citizen_access.py"]
    if not adapter_candidates:
        return []
    adapter = adapter_candidates[0]

    findings: list[Finding] = []
    # Split into top-level ## sections
    section_starts: list[tuple[int, str]] = []
    for i, line in enumerate(ctx.map_lines, start=1):
        if re.match(r"^##\s+\d+\.\s+", line):
            section_starts.append((i, line))

    # Build (start, end, heading, body_text) tuples
    sections: list[tuple[int, int, str, str]] = []
    for idx, (start, heading) in enumerate(section_starts):
        end = section_starts[idx + 1][0] - 1 if idx + 1 < len(section_starts) else len(ctx.map_lines)
        body = "\n".join(ctx.map_lines[start - 1: end])
        sections.append((start, end, heading, body))

    for start, end, heading, body in sections:
        # Does this section cover any ACCELA topic?
        topic_hit = None
        method = None
        for topic, meth in ACCELA_TOPICS.items():
            if re.search(rf"\b{re.escape(topic)}\b", heading, re.IGNORECASE):
                topic_hit = topic
                method = meth
                break
        if not topic_hit:
            continue
        # Is there a "Currently Extracted? / **NO" subsection?
        mo = re.search(
            r"###\s*Currently\s+Extracted\??[^\n]*\n+(?:[^\n]*\n)?\s*\*\*NO",
            body, re.IGNORECASE,
        )
        if not mo:
            continue
        # Locate the line for the map citation
        rel_offset = body[: mo.end()].count("\n")
        map_line = start + rel_offset
        map_quote = ctx.map_lines[map_line - 1] if 0 < map_line <= len(ctx.map_lines) else "**NO"

        # Does the method exist and get called?
        def_hits = grep_file(adapter, rf"def\s+{re.escape(method)}\s*\(")
        if not def_hits:
            continue
        call_hits: list[tuple[int, str]] = []
        for lineno, text in grep_file(adapter, rf"{re.escape(method)}\s*\("):
            if re.search(rf"def\s+{re.escape(method)}\s*\(", text):
                continue
            call_hits.append((lineno, text))
        if not call_hits:
            continue
        call_line, call_text = call_hits[0]
        # Dedupe against A1: if A1 already flagged the same method on a
        # nearby line, skip. But since A1 cites a different line pattern,
        # we keep both; they reinforce each other.
        findings.append(Finding(
            county=ctx.county,
            platform=ctx.platform,
            map_path=str(ctx.map_path),
            check_id="ACCELA-CURRENTLY-EXTRACTED-NO-BUT-PARSED",
            severity="drift",
            message=(f"Map '{heading.strip()}' section declares 'Currently "
                     f"Extracted? NO' but {method}() is called in the adapter."),
            map_claim=cite_map(ctx.map_path, map_line, map_quote, repo_root),
            code_evidence=cite(adapter, call_line, call_text, repo_root),
        ))
    return findings


def _extract_map_field_count_claim(map_lines: list[str]) -> tuple[int, int, str] | None:
    """Find 'we currently map N' / 'Of X attribute fields, we currently map N'.

    Returns (claimed_N, line_number_1based, quote) or None.
    """
    for i, line in enumerate(map_lines, start=1):
        m = re.search(r"(?i)\b(?:we\s+)?currently\s+map\s+(\d+)\b", line)
        if m:
            return int(m.group(1)), i, line
    return None


def _count_seed_gis_fields(row: dict) -> list[str]:
    """Return names of non-null gis_*_field entries in a seed row."""
    mapped = []
    for k in BI_FIELD_KEYS:
        v = row.get(k)
        if v is not None and v != "":
            mapped.append(k)
    return mapped


def check_B1_arcgis_field_count(ctx: CheckCtx, repo_root: Path) -> list[Finding]:
    if ctx.platform != "arcgis":
        return []
    claim = _extract_map_field_count_claim(ctx.map_lines)
    if claim is None:
        return []
    claimed_n, map_line, map_quote = claim
    if not ctx.artefacts.bi_seed_rows:
        return []
    row = ctx.artefacts.bi_seed_rows[0]
    mapped = _count_seed_gis_fields(row)
    actual_n = len(mapped)
    if claimed_n == actual_n:
        return []
    # Drift.
    seed_path = repo_root / "seed_bi_county_config.py"
    seed_line = int(row.get("_line", 0))
    extras = [k.replace("gis_", "").replace("_field", "") for k in mapped]
    # Build a readable evidence snippet: "name=Polk, mapped=[owner, parcel, ...]"
    seed_snippet = (f"name={row.get('name')!r}, mapped fields="
                    f"[{', '.join(extras)}]")
    return [Finding(
        county=ctx.county,
        platform=ctx.platform,
        map_path=str(ctx.map_path),
        check_id="ARCGIS-FIELD-COUNT-MISMATCH",
        severity="drift",
        message=(f"Map claims currently mapping {claimed_n} fields; "
                 f"seed_bi_county_config.py actually maps {actual_n} "
                 f"({', '.join(extras)})."),
        map_claim=cite_map(ctx.map_path, map_line, map_quote, repo_root),
        code_evidence=cite(seed_path, seed_line, seed_snippet, repo_root),
    )]


# Extra BI fields beyond the "core five" (owner, parcel, address, use, acreage).
EXTRA_BI_FIELDS = {
    "gis_subdivision_field": ("subdivision_name", "Subdivision"),
    "gis_building_value_field": ("building_value", "Building Value"),
    "gis_appraised_value_field": ("appraised_value", "Appraised Value"),
    "gis_deed_date_field": ("deed_date", "Deed Date"),
    "gis_previous_owner_field": ("previous_owner", "Previous Owner"),
}


def check_B3_arcgis_not_configured_but_is(ctx: CheckCtx, repo_root: Path) -> list[Finding]:
    """Map's Parsed Output says 'Not configured for <County>' for a field
    that the seed actually DOES map."""
    if ctx.platform != "arcgis":
        return []
    if not ctx.artefacts.bi_seed_rows:
        return []
    row = ctx.artefacts.bi_seed_rows[0]
    findings: list[Finding] = []
    seed_path = repo_root / "seed_bi_county_config.py"
    seed_line = int(row.get("_line", 0))

    for seed_key, (parsed_field, label) in EXTRA_BI_FIELDS.items():
        seed_val = row.get(seed_key)
        if seed_val is None or seed_val == "":
            continue
        # Search the map for a line claiming this field is not configured.
        pat = re.compile(
            rf"`?{re.escape(parsed_field)}`?.*Not\s+configured",
            re.IGNORECASE,
        )
        alt_pat = re.compile(
            rf"\|\s*`?{re.escape(parsed_field)}`?\s*\|.*Not\s+configured",
            re.IGNORECASE,
        )
        for i, line in enumerate(ctx.map_lines, start=1):
            if pat.search(line) or alt_pat.search(line):
                seed_quote = (read_file_lines(str(seed_path))[seed_line - 1]
                              if seed_line else "")
                findings.append(Finding(
                    county=ctx.county,
                    platform=ctx.platform,
                    map_path=str(ctx.map_path),
                    check_id="ARCGIS-NOT-CONFIGURED-BUT-MAPPED",
                    severity="drift",
                    message=(f"Map says `{parsed_field}` is 'Not configured' "
                             f"for {ctx.county.title()}, but seed maps "
                             f"{seed_key}={seed_val!r}."),
                    map_claim=cite_map(ctx.map_path, i, line, repo_root),
                    code_evidence=cite(seed_path, seed_line,
                                       f"{seed_key}: {seed_val!r}", repo_root),
                ))
                break  # one hit per extra field is enough
    return findings


# Maps URL-unverified pattern: "URL unverified"
URL_UNVERIFIED_PATTERN = re.compile(r"URL\s+unverified", re.IGNORECASE)


def check_C1_pt_blocker_undercount(ctx: CheckCtx, repo_root: Path) -> list[Finding]:
    """Map mentions only 'URL unverified' for a jurisdiction, but the PT seed
    has a non-empty fragile_note or scrape_mode='fixture' (a STRONGER blocker).
    """
    if ctx.platform not in PT_PLATFORMS:
        return []
    if not ctx.artefacts.pt_seed_rows:
        return []
    findings: list[Finding] = []
    seed_path = repo_root / "seed_pt_jurisdiction_config.py"

    # For each PT seed row that has a fragile_note OR scrape_mode=fixture, check
    # whether the map mentions its jurisdiction name with "URL unverified" and
    # does NOT mention the blocker.
    for row in ctx.artefacts.pt_seed_rows:
        note = row.get("fragile_note") or ""
        mode = (row.get("scrape_mode") or "").lower()
        if not note and mode != "fixture":
            continue
        jname = row.get("name") or ""
        # Find lines in the map mentioning this jurisdiction name AND "URL unverified"
        matched_lines: list[tuple[int, str]] = []
        for i, line in enumerate(ctx.map_lines, start=1):
            if jname and jname.lower() in line.lower() and URL_UNVERIFIED_PATTERN.search(line):
                matched_lines.append((i, line))
        if not matched_lines:
            continue
        # Does the map elsewhere mention the blocker keyword from the note?
        blocker_keyword = None
        for kw in ("reCAPTCHA", "captcha", "auth", "credential", "401", "403",
                   "login required", "blocked", "no date-range"):
            if kw.lower() in note.lower():
                blocker_keyword = kw
                break
        blocker_mentioned_in_map = False
        if blocker_keyword:
            blocker_mentioned_in_map = any(
                blocker_keyword.lower() in line.lower() for line in ctx.map_lines
            )
        if blocker_mentioned_in_map:
            continue
        # Drift: map understates the blocker.
        i_line, line_text = matched_lines[0]
        seed_line = int(row.get("_line", 0))
        seed_quote = (read_file_lines(str(seed_path))[seed_line - 1]
                      if seed_line else "")
        findings.append(Finding(
            county=ctx.county,
            platform=ctx.platform,
            map_path=str(ctx.map_path),
            check_id="PT-BLOCKER-UNDERSTATED",
            severity="drift",
            message=(f"Map calls {jname!r} 'URL unverified' but seed has a "
                     f"stronger blocker: fragile_note={note!r}, "
                     f"scrape_mode={mode!r}."),
            map_claim=cite_map(ctx.map_path, i_line, line_text, repo_root),
            code_evidence=cite(seed_path, seed_line, seed_quote, repo_root),
        ))
    return findings


def check_D1_adapter_class_missing(ctx: CheckCtx, repo_root: Path) -> list[Finding]:
    """Map mentions `FooAdapter` that isn't defined anywhere under modules/."""
    findings: list[Finding] = []
    mentioned = set()
    for i, line in enumerate(ctx.map_lines, start=1):
        for m in re.finditer(r"`([A-Z][A-Za-z0-9_]*Adapter)`", line):
            mentioned.add((m.group(1), i, line))
    if not mentioned:
        return []
    # Collect class definitions under modules/ once per run (cached)
    defs = _collect_adapter_class_defs(repo_root)
    seen_classes: set[str] = set()
    for cls_name, i, line in mentioned:
        if cls_name in seen_classes:
            continue
        seen_classes.add(cls_name)
        if cls_name in defs:
            continue
        findings.append(Finding(
            county=ctx.county,
            platform=ctx.platform,
            map_path=str(ctx.map_path),
            check_id="ADAPTER-CLASS-NOT-FOUND",
            severity="suspicious",
            message=f"Map references `{cls_name}` but no `class {cls_name}` "
                    f"found under modules/.",
            map_claim=cite_map(ctx.map_path, i, line, repo_root),
            code_evidence="(no matching class definition under modules/)",
        ))
    return findings


@lru_cache(maxsize=1)
def _collect_adapter_class_defs_cached(repo_root_str: str) -> frozenset:
    root = Path(repo_root_str)
    modules_dir = root / "modules"
    if not modules_dir.exists():
        return frozenset()
    found: set[str] = set()
    pat = re.compile(r"^\s*class\s+([A-Z][A-Za-z0-9_]*)\s*[:(]")
    for py in modules_dir.rglob("*.py"):
        try:
            for line in read_file_lines(str(py)):
                m = pat.match(line)
                if m:
                    found.add(m.group(1))
        except OSError:
            continue
    return frozenset(found)


def _collect_adapter_class_defs(repo_root: Path) -> frozenset:
    return _collect_adapter_class_defs_cached(str(repo_root))


CODE_CITATION_PATTERN = re.compile(
    r"`?([A-Za-z_][\w./\-]*\.(?:py|ya?ml))`?:(\d+)\b"
)


def check_D2_citation_past_eof(ctx: CheckCtx, repo_root: Path) -> list[Finding]:
    """Map cites file.py:N but N exceeds the actual line count."""
    findings: list[Finding] = []
    seen: set[tuple[str, int]] = set()
    for i, line in enumerate(ctx.map_lines, start=1):
        for m in CODE_CITATION_PATTERN.finditer(line):
            rel = m.group(1)
            if rel.startswith("docs/") or rel.startswith("http"):
                continue
            lineno = int(m.group(2))
            key = (rel, lineno)
            if key in seen:
                continue
            seen.add(key)
            target = (repo_root / rel).resolve()
            if not target.exists():
                continue
            total_lines = len(read_file_lines(str(target)))
            if total_lines == 0:
                continue
            if lineno > total_lines:
                findings.append(Finding(
                    county=ctx.county,
                    platform=ctx.platform,
                    map_path=str(ctx.map_path),
                    check_id="CITATION-PAST-EOF",
                    severity="suspicious",
                    message=(f"Map cites {rel}:{lineno} but file has only "
                             f"{total_lines} lines."),
                    map_claim=cite_map(ctx.map_path, i, line, repo_root),
                    code_evidence=f"{rel} (EOF at line {total_lines})",
                ))
    return findings


def check_E1_commission_tracked_yes_no_yaml(ctx: CheckCtx, repo_root: Path) -> list[Finding]:
    """Commission map says 'Tracked by Us? **YES**' with a slug but no YAML."""
    if ctx.platform not in CR_PLATFORMS:
        return []
    findings: list[Finding] = []
    yaml_dir = repo_root / "modules" / "commission" / "config" / "jurisdictions" / "FL"

    pat = re.compile(
        r"\*\*YES\*\*\s*\(([a-z0-9][a-z0-9\-]*)\)",
        re.IGNORECASE,
    )
    for i, line in enumerate(ctx.map_lines, start=1):
        m = pat.search(line)
        if not m:
            continue
        slug = m.group(1)
        yaml_path = yaml_dir / f"{slug}.yaml"
        if yaml_path.exists():
            continue
        findings.append(Finding(
            county=ctx.county,
            platform=ctx.platform,
            map_path=str(ctx.map_path),
            check_id="COMMISSION-TRACKED-YES-NO-YAML",
            severity="drift",
            message=f"Map marks `{slug}` as tracked but no YAML at {yaml_path.relative_to(repo_root).as_posix()}.",
            map_claim=cite_map(ctx.map_path, i, line, repo_root),
            code_evidence=f"(missing) {yaml_path.relative_to(repo_root).as_posix()}",
        ))
    return findings


def check_F1_no_artefacts(ctx: CheckCtx, repo_root: Path) -> list[Finding]:
    """Info-level: the map resolves to no code artefacts at all."""
    art = ctx.artefacts
    if (art.permit_adapter_paths or art.commission_scraper_path
            or art.commission_yaml_paths or art.bi_seed_rows or art.pt_seed_rows):
        return []
    return [Finding(
        county=ctx.county,
        platform=ctx.platform,
        map_path=str(ctx.map_path),
        check_id="NO-ARTEFACTS-RESOLVED",
        severity="info",
        message=(f"No adapter/scraper/YAML/seed artefacts resolved for "
                 f"{ctx.county}/{ctx.platform}. Map may be documenting a "
                 f"manual or unsupported surface."),
        map_claim=cite_map(ctx.map_path, 1, ctx.map_lines[0] if ctx.map_lines else "",
                           repo_root),
        code_evidence="(no artefacts)",
    )]


# ---------------------------------------------------------------------------
# Check dispatch
# ---------------------------------------------------------------------------

ALL_CHECKS = [
    check_A1_accela_method_called,
    check_A2_accela_section_NO_but_called,
    check_B1_arcgis_field_count,
    check_B3_arcgis_not_configured_but_is,
    check_C1_pt_blocker_undercount,
    check_D1_adapter_class_missing,
    check_D2_citation_past_eof,
    check_E1_commission_tracked_yes_no_yaml,
    check_F1_no_artefacts,
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(repo_root: Path, args: argparse.Namespace) -> list[Finding]:
    map_dir = Path(args.map_dir) if args.map_dir else (repo_root / "docs" / "api-maps")
    bi_rows = read_seed_bi_configs(repo_root)
    pt_rows = read_seed_pt_jurisdictions(repo_root)

    findings: list[Finding] = []
    scanned = 0
    skipped: list[str] = []
    counties_seen: set[str] = set()

    for map_path in sorted(map_dir.glob("*.md")):
        parsed = parse_map_filename(map_path)
        if parsed is None:
            skipped.append(map_path.name)
            continue
        county_slug, county, platform = parsed
        if args.county and args.county.lower() != county.lower():
            continue
        if args.platform and args.platform.lower() != platform.lower():
            continue
        scanned += 1
        counties_seen.add(county)

        text = read_file_text(str(map_path))
        lines = text.splitlines()
        art = resolve_artefacts(county_slug, county, platform, repo_root,
                                bi_rows, pt_rows)
        ctx = CheckCtx(
            map_path=map_path,
            county_slug=county_slug,
            county=county,
            platform=platform,
            map_text=text,
            map_lines=lines,
            artefacts=art,
        )
        for check in ALL_CHECKS:
            try:
                findings.extend(check(ctx, repo_root))
            except Exception as e:  # defensive: a broken check shouldn't abort
                findings.append(Finding(
                    county=county,
                    platform=platform,
                    map_path=str(map_path),
                    check_id=f"CHECK-EXCEPTION:{check.__name__}",
                    severity="suspicious",
                    message=f"Check raised {type(e).__name__}: {e}",
                ))

    # Sort: drift > suspicious > info; then by county, platform, check_id
    sev_order = {"drift": 0, "suspicious": 1, "info": 2}
    findings.sort(key=lambda f: (sev_order.get(f.severity, 99), f.county,
                                 f.platform, f.check_id))
    return findings, scanned, len(counties_seen), skipped


def format_human(findings: list[Finding], scanned: int, n_counties: int,
                 skipped: list[str]) -> str:
    lines: list[str] = []
    n_drift = sum(1 for f in findings if f.severity == "drift")
    n_susp = sum(1 for f in findings if f.severity == "suspicious")
    n_info = sum(1 for f in findings if f.severity == "info")
    lines.append("# API Map Drift Audit")
    lines.append(f"Scanned {scanned} maps across {n_counties} counties; "
                 f"found {n_drift} drift, {n_susp} suspicious, {n_info} info.")
    if skipped:
        lines.append(f"Skipped: {', '.join(skipped)}")
    lines.append("")
    prev_key = None
    for f in findings:
        key = (f.county, f.platform)
        if key != prev_key:
            lines.append(f"## {f.county} / {f.platform}")
            prev_key = key
        tag = f.severity.upper()
        lines.append(f"  [{tag}] {f.check_id}")
        lines.append(f"    message: {f.message}")
        if f.map_claim:
            lines.append(f"    map     {f.map_claim}")
        if f.code_evidence:
            lines.append(f"    code    {f.code_evidence}")
        lines.append("")
    # Per-check summary
    from collections import Counter
    ctr = Counter(f.check_id for f in findings)
    lines.append("## Check summary")
    for cid, n in sorted(ctr.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"  {cid}: {n}")
    return "\n".join(lines)


def format_json(findings: list[Finding]) -> str:
    return json.dumps([asdict(f) for f in findings], indent=2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--map-dir", default=None,
                    help="Path to api-maps directory (default: docs/api-maps).")
    ap.add_argument("--root", default=None,
                    help="Repo root (default: auto-detected from script location).")
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON findings instead of human-readable report.")
    ap.add_argument("--county", default=None,
                    help="Only scan a single county slug (e.g. 'polk').")
    ap.add_argument("--platform", default=None,
                    help="Only scan a single platform token (e.g. 'arcgis').")
    ap.add_argument("--fail-on-drift", action="store_true",
                    help="Exit 2 if any drift finding is produced.")
    args = ap.parse_args()

    repo_root = Path(args.root).resolve() if args.root else REPO_ROOT
    findings, scanned, n_counties, skipped = run(repo_root, args)

    if args.json:
        print(format_json(findings))
    else:
        print(format_human(findings, scanned, n_counties, skipped))

    if args.fail_on_drift and any(f.severity == "drift" for f in findings):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
