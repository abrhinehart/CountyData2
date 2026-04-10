"""Jurisdiction and state YAML config loader.

Ported from Commission Radar. The YAML config files live under
``modules/commission/config/`` (jurisdictions/<state>/<slug>.yaml and
states/<state>.yaml). ``CONFIG_DIR`` comes from the module-local config.

The seed script ``seed_cr_jurisdiction_config.py`` already writes these
configs into ``cr_jurisdiction_config``, so ``sync_jurisdictions_to_db``
is intentionally not ported — the extractor and auto_detect callers only
use the read-only helpers below.
"""

import logging
from pathlib import Path

import yaml

from modules.commission.config import CONFIG_DIR

logger = logging.getLogger("commission_radar.config_loader")

# Entitlement types in display order (used to build terminology block for prompts)
ENTITLEMENT_TYPES = [
    ("annexation", "Annexation"),
    ("comprehensive_plan_amendment", "Comprehensive plan / land use amendment (small-scale < 50 acres, large-scale >= 50 acres)"),
    ("rezoning", "Rezoning / zone change (includes PUD districts)"),
    ("development_review", "Development review / major development approval (Planning Board)"),
    ("subdivision", "Subdivision plat (preliminary, final)"),
    ("developer_agreement", "Developer agreement"),
    ("conditional_use", "Special / conditional use permit"),
    ("text_amendment", "Text / code amendment"),
]


def _config_dir() -> Path:
    """Return the config directory path."""
    return Path(CONFIG_DIR)


def load_state_config(state_code: str) -> dict:
    """Load state-level configuration.

    Falls back to _default.yaml if the state has no config file.
    """
    states_dir = _config_dir() / "states"
    state_file = states_dir / f"{state_code}.yaml"

    if state_file.exists():
        with open(state_file, "r") as f:
            return yaml.safe_load(f)

    default_file = states_dir / "_default.yaml"
    if default_file.exists():
        with open(default_file, "r") as f:
            config = yaml.safe_load(f)
            logger.info("No state config for %s, using default", state_code)
            return config

    return {"state": state_code, "terminology": {}, "case_number_formats": []}


def _apply_defaults(config: dict, yaml_file_path: Path) -> dict:
    """Merge state-level defaults for missing keys (e.g. keywords).

    Looks for a file named _{state_code}-defaults.yaml in the same directory.
    Only merges keys that are absent from the jurisdiction config.
    """
    state_code = config.get("state", "").lower()
    if not state_code:
        return config

    defaults_file = yaml_file_path.parent / f"_{state_code}-defaults.yaml"
    if not defaults_file.exists():
        candidates = list(yaml_file_path.parent.glob("_*-defaults.yaml"))
        candidates = [c for c in candidates if c != yaml_file_path]
        defaults_file = candidates[0] if candidates else None
    if not defaults_file or not defaults_file.exists() or defaults_file == yaml_file_path:
        return config

    with open(defaults_file, "r") as f:
        defaults = yaml.safe_load(f) or {}

    if "keywords" not in config and "keywords" in defaults:
        config["keywords"] = defaults["keywords"]

    return config


def load_jurisdiction_config(slug: str) -> dict | None:
    """Load jurisdiction configuration by slug.

    Searches config/jurisdictions/**/{slug}.yaml.
    """
    jurisdictions_dir = _config_dir() / "jurisdictions"
    if not jurisdictions_dir.exists():
        return None

    for yaml_file in jurisdictions_dir.rglob(f"{slug}.yaml"):
        with open(yaml_file, "r") as f:
            config = yaml.safe_load(f)
        if config:
            config = _apply_defaults(config, yaml_file)
        return config

    return None


def load_all_jurisdictions() -> list[dict]:
    """Load all jurisdiction configuration files."""
    jurisdictions_dir = _config_dir() / "jurisdictions"
    if not jurisdictions_dir.exists():
        return []

    configs: list[dict] = []
    for yaml_file in sorted(jurisdictions_dir.rglob("*.yaml")):
        with open(yaml_file, "r") as f:
            config = yaml.safe_load(f)
            if config and "slug" in config:
                config = _apply_defaults(config, yaml_file)
                configs.append(config)

    return configs


def get_extraction_context(slug: str) -> dict:
    """Build the full extraction context for a jurisdiction.

    Merges state-level terminology with jurisdiction-specific notes.
    """
    juris_config = load_jurisdiction_config(slug)
    if juris_config is None:
        raise ValueError(f"No jurisdiction config found for slug: {slug}")

    state_code = juris_config.get("state", "__default__")
    state_config = load_state_config(state_code)

    terminology = state_config.get("terminology", {})
    case_formats = state_config.get("case_number_formats", [])
    extraction_notes = juris_config.get("extraction_notes", [])

    terminology_lines = []
    for type_key, type_label in ENTITLEMENT_TYPES:
        local_terms = terminology.get(type_key, [])
        if local_terms:
            terms_str = ", ".join(f'"{t}"' for t in local_terms)
            terminology_lines.append(f"- {type_label} (local terms: {terms_str})")
        else:
            terminology_lines.append(f"- {type_label}")
    terminology_block = "\n".join(terminology_lines)

    jurisdiction_notes_block = ""
    if extraction_notes:
        notes_str = "\n".join(f"- {note}" for note in extraction_notes)
        jurisdiction_notes_block = (
            f"JURISDICTION-SPECIFIC NOTES for {juris_config['name']}:\n{notes_str}"
        )

    case_number_formats_block = ""
    if case_formats:
        format_lines = []
        for entry in case_formats:
            if isinstance(entry, dict):
                pattern = entry.get("pattern", "")
                description = entry.get("description")
                if description:
                    format_lines.append(f"- {description}: `{pattern}`")
                elif pattern:
                    format_lines.append(f"- `{pattern}`")
            elif entry:
                format_lines.append(f"- `{entry}`")
        if format_lines:
            case_number_formats_block = (
                "COMMON CASE / ORDINANCE NUMBER FORMATS:\n"
                + "\n".join(format_lines)
            )

    return {
        "state": state_code,
        "jurisdiction_name": juris_config["name"],
        "jurisdiction_slug": slug,
        "terminology": terminology,
        "case_number_formats": case_formats,
        "case_number_formats_block": case_number_formats_block,
        "extraction_notes": extraction_notes,
        "terminology_block": terminology_block,
        "jurisdiction_notes_block": jurisdiction_notes_block,
    }
