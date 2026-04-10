import re


DEFAULT_WEIGHTS = {
    "strong": 3,
    "medium": 2,
    "weak": 1,
}
PASS_SCORE_THRESHOLD = 4
MEDIUM_MATCH_THRESHOLD = 2
EARLY_LINE_LIMIT = 60
HEADING_BONUS = 1
EARLY_LINE_BONUS = 1
MAX_EVIDENCE_LENGTH = 120
STRONG_TERMS = {
    "annexation",
    "annex",
    "rezoning",
    "zone change",
    "developer agreement",
    "reimbursement agreement",
    "quasi judicial",
    "quasi-judicial",
    "dri",
    "pud",
    "dsap",
    "cpc pln",
    "cpc-pln",
    "mdev",
    "major development",
}
WEAK_TERMS = {
    "lots",
    "units",
    "acres",
    "dwelling",
    "residential",
    "public hearing",
    "ordinance",
    "developer",
}
DEFAULT_GATES = {
    "public hearing": [
        "annexation",
        "annex",
        "rezoning",
        "zone change",
        "land use",
        "future land use",
        "comprehensive plan",
        "flum",
        "developer agreement",
        "reimbursement agreement",
        "quasi judicial",
        "quasi-judicial",
        "subdivision",
        "plat",
        "dri",
        "pud",
        "dsap",
        "major development",
        "cpc pln",
        "cpc-pln",
        "mdev",
    ],
    "ordinance": [
        "annexation",
        "annex",
        "rezoning",
        "zone change",
        "land use",
        "future land use",
        "comprehensive plan",
        "flum",
        "developer agreement",
        "reimbursement agreement",
        "quasi judicial",
        "quasi-judicial",
        "subdivision",
        "plat",
        "major development",
        "cpc pln",
        "cpc-pln",
        "mdev",
    ],
    "lots": [
        "subdivision",
        "plat",
        "annexation",
        "annex",
        "rezoning",
        "zone change",
        "land use",
        "future land use",
        "comprehensive plan",
        "flum",
        "dri",
        "pud",
        "dsap",
        "major development",
    ],
    "units": [
        "subdivision",
        "plat",
        "annexation",
        "annex",
        "rezoning",
        "zone change",
        "land use",
        "future land use",
        "comprehensive plan",
        "flum",
        "dri",
        "pud",
        "dsap",
        "major development",
    ],
    "acres": [
        "subdivision",
        "plat",
        "annexation",
        "annex",
        "rezoning",
        "zone change",
        "land use",
        "future land use",
        "comprehensive plan",
        "flum",
        "dri",
        "pud",
        "dsap",
        "major development",
    ],
    "dwelling": [
        "subdivision",
        "plat",
        "annexation",
        "annex",
        "rezoning",
        "zone change",
        "land use",
        "future land use",
        "comprehensive plan",
        "flum",
        "dri",
        "pud",
        "dsap",
        "major development",
    ],
    "residential": [
        "subdivision",
        "plat",
        "annexation",
        "annex",
        "rezoning",
        "zone change",
        "land use",
        "future land use",
        "comprehensive plan",
        "flum",
        "dri",
        "pud",
        "dsap",
        "major development",
    ],
}


def _normalize_term_key(value):
    return " ".join(re.sub(r"[\s\-]+", " ", value.strip().lower()).split())


def _compile_term_pattern(term):
    parts = [re.escape(part) for part in re.split(r"[\s\-]+", term.strip()) if part]
    escaped = r"[\s\-]+".join(parts)
    return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)


def _infer_strength(term):
    normalized = _normalize_term_key(term)
    if normalized in STRONG_TERMS:
        return "strong"
    if normalized in WEAK_TERMS:
        return "weak"
    return "medium"


def _looks_like_heading(line):
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return False

    letters = [char for char in stripped if char.isalpha()]
    if not letters:
        return False

    uppercase_ratio = sum(1 for char in letters if char.isupper()) / len(letters)
    if uppercase_ratio >= 0.6:
        return True

    heading_phrases = (
        "AGENDA",
        "PUBLIC HEARING",
        "CONSENT",
        "QUASI",
        "ANNEXATION",
        "REZONING",
        "LAND USE",
        "SUBDIVISION",
        "PLAT",
        "ORDINANCE",
    )
    upper_line = stripped.upper()
    return any(phrase in upper_line for phrase in heading_phrases)


def _truncate_evidence(line):
    compact = " ".join(line.strip().split())
    if len(compact) <= MAX_EVIDENCE_LENGTH:
        return compact
    return f"{compact[:MAX_EVIDENCE_LENGTH - 3]}..."


def _normalize_rule(raw_rule):
    if isinstance(raw_rule, str):
        term = raw_rule
        strength = _infer_strength(term)
        requires_any = DEFAULT_GATES.get(_normalize_term_key(term), [])
        excludes_any = []
    else:
        term = raw_rule["term"]
        strength = raw_rule.get("strength") or _infer_strength(term)
        requires_any = raw_rule.get("requires_any", DEFAULT_GATES.get(_normalize_term_key(term), []))
        excludes_any = raw_rule.get("excludes_any", [])

    return {
        "term": term,
        "term_key": _normalize_term_key(term),
        "strength": strength,
        "weight": DEFAULT_WEIGHTS[strength],
        "pattern": _compile_term_pattern(term),
        "requires_any": requires_any,
        "requires_any_keys": {_normalize_term_key(value) for value in requires_any},
        "excludes_any": excludes_any,
        "excludes_any_keys": {_normalize_term_key(value) for value in excludes_any},
    }


def _load_keyword_rules(config):
    raw_rules = config.get("keyword_rules")
    if raw_rules:
        return [_normalize_rule(rule) for rule in raw_rules]
    return [_normalize_rule(rule) for rule in config.get("keywords", [])]


def _find_rule_match(rule, lines):
    best_match = None
    for index, line in enumerate(lines):
        match = rule["pattern"].search(line)
        if not match:
            continue

        score = rule["weight"]
        bonuses = []
        if index < EARLY_LINE_LIMIT:
            score += EARLY_LINE_BONUS
            bonuses.append("early document match")
        if _looks_like_heading(line):
            score += HEADING_BONUS
            bonuses.append("section heading match")

        candidate = {
            "term": rule["term"],
            "term_key": rule["term_key"],
            "strength": rule["strength"],
            "weight": rule["weight"],
            "score": score,
            "line_number": index + 1,
            "evidence": _truncate_evidence(line),
            "bonuses": bonuses,
            "requires_any": list(rule["requires_any"]),
            "requires_any_keys": set(rule["requires_any_keys"]),
            "excludes_any": list(rule["excludes_any"]),
            "excludes_any_keys": set(rule["excludes_any_keys"]),
        }
        if best_match is None or candidate["score"] > best_match["score"] or (
            candidate["score"] == best_match["score"] and candidate["line_number"] < best_match["line_number"]
        ):
            best_match = candidate

    return best_match


def _build_reason(passed, total_score, strong_matches, medium_matches, matched_terms, blocked_terms):
    if passed:
        if strong_matches:
            return f"Passed on strong keyword match: {', '.join(strong_matches[:3])}."
        if len(medium_matches) >= MEDIUM_MATCH_THRESHOLD:
            return f"Passed on multiple medium-signal matches: {', '.join(medium_matches[:3])}."
        return f"Passed on combined keyword score {total_score}/{PASS_SCORE_THRESHOLD}."

    if blocked_terms and not matched_terms:
        return "Only gated or noisy terms matched without supporting development signals."
    if matched_terms:
        return (
            f"Keyword score {total_score}/{PASS_SCORE_THRESHOLD}; "
            f"no strong matches and only {len(medium_matches)} medium-signal match(es)."
        )
    return "No jurisdiction keywords matched."


def format_keyword_filter_detail(result: dict) -> str:
    """Return a human-readable keyword filter summary."""
    if result.get("auto_passed"):
        return "Keyword filter auto-passed because no keywords are configured."

    parts = [f"Score {result['score']}/{result['threshold']}"]
    for strength in ("strong", "medium", "weak"):
        matched = result["matched_by_strength"].get(strength, [])
        if matched:
            parts.append(f"{strength.title()}: {', '.join(matched[:5])}")
    if result.get("matched_terms"):
        evidence = "; ".join(
            f"{item['term']} @ line {item['line_number']}: \"{item['evidence']}\""
            for item in result["matched_terms"][:2]
        )
        parts.append(f"Evidence: {evidence}")
    if result.get("blocked_terms"):
        blocked = "; ".join(
            f"{item['term']} ({item['reason']})" for item in result["blocked_terms"][:2]
        )
        parts.append(f"Blocked noisy terms: {blocked}")
    parts.append(result["reason"])
    return ". ".join(parts)


def check_keywords(text: str, jurisdiction_config: dict) -> dict:
    """Check if extracted text contains enough development signals to continue.

    Args:
        text: Extracted document text.
        jurisdiction_config: Loaded jurisdiction YAML config dict
            (as returned by ``config_loader.load_jurisdiction_config``).
            May be empty; an empty dict is treated as "no rules configured"
            and auto-passes.

    Returns:
        dict with keys including:
            passed, matched_keywords, matched_terms, matched_by_strength,
            blocked_terms, score, threshold, reason, auto_passed
    """
    rules = _load_keyword_rules(jurisdiction_config or {})

    if not rules:
        return {
            "passed": True,
            "matched_keywords": [],
            "matched_terms": [],
            "matched_by_strength": {"strong": [], "medium": [], "weak": []},
            "blocked_terms": [],
            "score": 0,
            "threshold": PASS_SCORE_THRESHOLD,
            "reason": "No keyword rules configured.",
            "auto_passed": True,
        }

    lines = text.splitlines()
    discovered_matches = []
    for rule in rules:
        match = _find_rule_match(rule, lines)
        if match:
            discovered_matches.append(match)

    matched_term_keys = {match["term_key"] for match in discovered_matches}
    accepted_matches = []
    blocked_terms = []

    for match in discovered_matches:
        supporting_matches = sorted(
            {
                other["term"]
                for other in discovered_matches
                if other["term_key"] != match["term_key"] and other["term_key"] in match["requires_any_keys"]
            }
        )
        conflicting_matches = sorted(
            {
                other["term"]
                for other in discovered_matches
                if other["term_key"] != match["term_key"] and other["term_key"] in match["excludes_any_keys"]
            }
        )

        if match["requires_any_keys"] and not supporting_matches:
            blocked_terms.append({
                "term": match["term"],
                "reason": f"needs one of: {', '.join(match['requires_any'][:5])}",
            })
            continue
        if match["excludes_any_keys"] and conflicting_matches:
            blocked_terms.append({
                "term": match["term"],
                "reason": f"blocked by: {', '.join(conflicting_matches[:5])}",
            })
            continue

        match["supporting_matches"] = supporting_matches
        accepted_matches.append(match)

    accepted_matches.sort(key=lambda item: (-item["score"], item["line_number"], item["term"].lower()))
    matched_by_strength = {
        "strong": [item["term"] for item in accepted_matches if item["strength"] == "strong"],
        "medium": [item["term"] for item in accepted_matches if item["strength"] == "medium"],
        "weak": [item["term"] for item in accepted_matches if item["strength"] == "weak"],
    }
    total_score = sum(item["score"] for item in accepted_matches)
    strong_matches = matched_by_strength["strong"]
    medium_matches = matched_by_strength["medium"]
    passed = (
        bool(strong_matches)
        or len(medium_matches) >= MEDIUM_MATCH_THRESHOLD
        or total_score >= PASS_SCORE_THRESHOLD
    )

    return {
        "passed": passed,
        "matched_keywords": [item["term"] for item in accepted_matches],
        "matched_terms": [
            {
                "term": item["term"],
                "strength": item["strength"],
                "weight": item["weight"],
                "score": item["score"],
                "line_number": item["line_number"],
                "evidence": item["evidence"],
                "bonuses": list(item["bonuses"]),
                "supporting_matches": list(item.get("supporting_matches", [])),
            }
            for item in accepted_matches
        ],
        "matched_by_strength": matched_by_strength,
        "blocked_terms": blocked_terms,
        "score": total_score,
        "threshold": PASS_SCORE_THRESHOLD,
        "reason": _build_reason(
            passed,
            total_score,
            strong_matches,
            medium_matches,
            accepted_matches,
            blocked_terms,
        ),
        "auto_passed": False,
    }
