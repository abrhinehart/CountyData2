import re
from datetime import datetime

from modules.commission.config_loader import load_all_jurisdictions, load_jurisdiction_config
from modules.commission.constants import (
    HEADER_NARROW_CHARS,
    HEADER_WIDE_CHARS,
)


MONTH_NAMES = (
    r"(?:January|February|March|April|May|June|July|"
    r"August|September|October|November|December)"
)

DATE_REGEX = re.compile(
    rf"({MONTH_NAMES})\s+(\d{{1,2}}),\s+(\d{{4}})", re.IGNORECASE
)

MEETING_KEYWORDS = ("MEETING", "AGENDA", "MINUTES")
ADMIN_DATE_KEYWORDS = ("POSTED", "PUBLISHED", "REVISED", "AMENDED", "APPROVED", "ADOPTED", "UPDATED")
JURISDICTION_SCORE_GAP = 2
DATE_SCORE_GAP = 2


def _dedupe_preserve_order(values):
    seen = set()
    ordered = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _score_gap(candidates):
    if not candidates:
        return 0
    if len(candidates) == 1:
        return candidates[0]["score"]
    return candidates[0]["score"] - candidates[1]["score"]


def _build_result(status, value, score, score_gap, reason, warnings, candidates):
    return {
        "status": status,
        "value": value,
        "score": score,
        "score_gap": score_gap,
        "reason": reason,
        "warnings": _dedupe_preserve_order(warnings),
        "candidates": candidates[:3],
    }


def _candidate_summary(candidate):
    if candidate.get("name"):
        return f"{candidate['name']} ({candidate['score']})"
    return f"{candidate['value']} ({candidate['score']})"


def format_detection_error(label: str, result: dict) -> str:
    if result["status"] == "ambiguous" and result["candidates"]:
        options = ", ".join(_candidate_summary(candidate) for candidate in result["candidates"][:2])
        return f"Could not confidently detect {label}. Top candidates: {options}."
    if result["status"] == "not_found":
        return f"Could not auto-detect {label}."
    return f"Could not confidently detect {label}."


def format_detection_success(label: str, value_display: str, result: dict) -> str:
    detail = f"{label}: {value_display} ({result['reason']})"
    if result["warnings"]:
        detail += f". Warnings: {'; '.join(result['warnings'])}"
    return detail


def _parse_date_match(match):
    """Parse a regex match with (month, day, year) groups into YYYY-MM-DD."""
    try:
        date_str = f"{match.group(1)} {match.group(2)}, {match.group(3)}"
        dt = datetime.strptime(date_str.title(), "%B %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def _line_ranges(text):
    ranges = []
    offset = 0
    for index, line in enumerate(text.splitlines(keepends=True)):
        ranges.append((index, offset, offset + len(line), line.rstrip("\r\n")))
        offset += len(line)
    if not ranges and text:
        ranges.append((0, 0, len(text), text))
    return ranges


def _find_line_index(line_ranges, position):
    for index, start, end, _ in line_ranges:
        if start <= position < end or (position == end and index == len(line_ranges) - 1):
            return index
    return None


def _normalized_pattern_values(values):
    return [str(value).upper() for value in values if value]


def _score_detection_patterns(patterns, text):
    wide_header_text = text[:HEADER_WIDE_CHARS].upper()
    header_zone = patterns.get("header_zone", "narrow")
    header_text = text[:HEADER_WIDE_CHARS].upper() if header_zone == "wide" else text[:HEADER_NARROW_CHARS].upper()

    header_keywords = _normalized_pattern_values(patterns.get("header_keywords", []))
    wide_keywords = _normalized_pattern_values(patterns.get("wide_keywords", []))
    role_keywords = _normalized_pattern_values(patterns.get("role_keywords", []))
    require_also = _normalized_pattern_values(patterns.get("require_also", []))
    exclude_keywords = _normalized_pattern_values(patterns.get("exclude_keywords", []))
    minimum_score = int(patterns.get("minimum_score", 3))

    matched_header_keywords = [keyword for keyword in header_keywords if keyword in header_text]
    matched_wide_keywords = [keyword for keyword in wide_keywords if keyword in wide_header_text]
    matched_role_keywords = [keyword for keyword in role_keywords if keyword in wide_header_text]
    matched_excludes = [keyword for keyword in exclude_keywords if keyword in wide_header_text]

    if not matched_header_keywords and not matched_wide_keywords and not matched_role_keywords:
        return None

    if require_also and not all(keyword in wide_header_text for keyword in require_also):
        return None

    score = 0
    reasons = []

    if matched_header_keywords:
        score += len(matched_header_keywords) * 3
        reasons.extend(
            f"matched header keyword '{keyword}' in {header_zone} header"
            for keyword in matched_header_keywords
        )
    if matched_wide_keywords:
        score += len(matched_wide_keywords) * 2
        reasons.extend(
            f"matched wide-header keyword '{keyword}'"
            for keyword in matched_wide_keywords
        )
    if matched_role_keywords:
        score += len(matched_role_keywords)
        reasons.extend(
            f"matched role keyword '{keyword}' in wide header"
            for keyword in matched_role_keywords
        )
    if require_also:
        score += 2
        reasons.append("matched all required wide-header terms")
    if matched_excludes:
        score -= len(matched_excludes) * 2
        reasons.extend(
            f"penalized by excluded keyword '{keyword}'"
            for keyword in matched_excludes
        )

    if score < minimum_score:
        return None

    return {
        "score": score,
        "reasons": reasons,
    }


def detect_jurisdiction_details(text: str) -> dict:
    """Score all jurisdiction candidates and return a structured result."""
    configs = load_all_jurisdictions()
    candidates = []

    for config in configs:
        patterns = config.get("detection_patterns", {})
        scored = _score_detection_patterns(patterns, text)
        if not scored:
            continue

        candidates.append({
            "value": config["slug"],
            "name": config["name"],
            "score": scored["score"],
            "reasons": scored["reasons"],
        })

    candidates.sort(key=lambda candidate: (-candidate["score"], candidate["value"]))
    if not candidates:
        return _build_result(
            "not_found",
            None,
            0,
            0,
            "No jurisdiction header patterns matched.",
            [],
            [],
        )

    top_candidate = candidates[0]
    gap = _score_gap(candidates)
    if len(candidates) > 1 and gap <= 1:
        return _build_result(
            "ambiguous",
            None,
            top_candidate["score"],
            gap,
            "Multiple jurisdictions matched with similar confidence.",
            [],
            candidates,
        )

    return _build_result(
        "ok",
        top_candidate["value"],
        top_candidate["score"],
        gap,
        "; ".join(top_candidate["reasons"]),
        [],
        candidates,
    )


def _add_date_evidence(evidence_map, date_value, score_delta, reason, *, warning=None):
    evidence = evidence_map.setdefault(date_value, {"score": 0, "reasons": [], "warnings": []})
    evidence["score"] += score_delta
    evidence["reasons"].append(reason)
    if warning:
        evidence["warnings"].append(warning)


def detect_meeting_date_details(text: str) -> dict:
    """Score all date candidates in the header window and return a structured result."""
    header_text = text[:HEADER_WIDE_CHARS]
    line_ranges = _line_ranges(header_text)
    evidence_map = {}

    for match in DATE_REGEX.finditer(header_text):
        date_value = _parse_date_match(match)
        if not date_value:
            continue

        position = match.start()
        line_index = _find_line_index(line_ranges, position)
        if line_index is None:
            continue

        current_line = line_ranges[line_index][3]
        previous_line = line_ranges[line_index - 1][3] if line_index > 0 else ""
        next_line = line_ranges[line_index + 1][3] if line_index + 1 < len(line_ranges) else ""
        nearby_lines = " ".join(line.upper() for line in (previous_line, current_line, next_line))
        current_line_upper = current_line.upper()
        previous_line_upper = previous_line.upper()
        next_line_upper = next_line.upper()

        _add_date_evidence(evidence_map, date_value, 1, "found in the wide header window")

        if position < HEADER_NARROW_CHARS:
            _add_date_evidence(evidence_map, date_value, 4, "found in the narrow header window")

        if any(keyword in current_line_upper for keyword in MEETING_KEYWORDS):
            _add_date_evidence(evidence_map, date_value, 3, "appeared on a meeting/agenda/minutes line")
        elif any(keyword in previous_line_upper for keyword in MEETING_KEYWORDS) or any(
            keyword in next_line_upper for keyword in MEETING_KEYWORDS
        ):
            _add_date_evidence(evidence_map, date_value, 2, "appeared adjacent to a meeting/agenda/minutes line")

        if any(keyword in nearby_lines for keyword in ADMIN_DATE_KEYWORDS):
            _add_date_evidence(
                evidence_map,
                date_value,
                -2,
                "appeared near administrative date text",
                warning="Selected date appeared near posted/revised metadata.",
            )

    if not evidence_map:
        return _build_result(
            "not_found",
            None,
            0,
            0,
            "No meeting date patterns matched.",
            [],
            [],
        )

    candidates = []
    for date_value, evidence in evidence_map.items():
        candidates.append({
            "value": date_value,
            "score": evidence["score"],
            "reasons": _dedupe_preserve_order(evidence["reasons"]),
            "warnings": _dedupe_preserve_order(evidence["warnings"]),
        })

    candidates.sort(key=lambda candidate: (-candidate["score"], candidate["value"]))
    top_candidate = candidates[0]
    gap = _score_gap(candidates)

    if len(candidates) > 1 and gap <= 1:
        return _build_result(
            "ambiguous",
            None,
            top_candidate["score"],
            gap,
            "Multiple dates matched with similar confidence.",
            [],
            candidates,
        )

    warnings = list(top_candidate["warnings"])
    if top_candidate["score"] >= 3 and gap >= DATE_SCORE_GAP:
        status = "ok"
    else:
        status = "weak"
        warnings.append("Meeting date relied on weak or fallback header evidence.")

    return _build_result(
        status,
        top_candidate["value"],
        top_candidate["score"],
        gap,
        "; ".join(top_candidate["reasons"]),
        warnings,
        candidates,
    )


def detect_jurisdiction(text: str) -> str | None:
    """Backward-compatible wrapper for jurisdiction auto-detection."""
    result = detect_jurisdiction_details(text)
    if result["status"] == "ok":
        return result["value"]
    return None


def detect_jurisdiction_name(text: str) -> str | None:
    """Backward-compatible wrapper that returns the detected jurisdiction name."""
    result = detect_jurisdiction_details(text)
    if result["status"] != "ok" or result["value"] is None:
        return None

    config = load_jurisdiction_config(result["value"])
    return config["name"] if config else None


def detect_meeting_date(text: str) -> str | None:
    """Backward-compatible wrapper for meeting-date auto-detection."""
    result = detect_meeting_date_details(text)
    if result["status"] in {"ok", "weak"}:
        return result["value"]
    return None
