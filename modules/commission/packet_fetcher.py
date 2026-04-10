"""CivicPlus agenda HTML parsing — backup PDF URLs and structured field extraction.

CivicPlus agendas served with ?html=true contain:
- Per-item backup PDFs (AGENDA REQUEST documents)
- For planning board agendas, structured description fields with acreage,
  applicant, address, application type, etc.
- For city commission agendas, ordinance titles that sometimes include acreage
"""

import logging
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("commission_radar.packet_fetcher")

_CIVICPLUS_AGENDA_RE = re.compile(r"/AgendaCenter/ViewFile/Agenda/")
_ORD_PREFIX_RE = re.compile(r"^(?:ord(?:inance)?)\s*(?:no\.?\s*)?", re.IGNORECASE)
_ACREAGE_IN_TITLE_RE = re.compile(
    r"approximately\s+([\d,.]+)\s*acres", re.IGNORECASE
)
_PARCEL_ID_RE = re.compile(r"Parcel\s*(?:ID\s*)?#?:?\s*([\d-]+)", re.IGNORECASE)


# ── Shared helpers ────────────────────────────────────────────────────────


def _build_match_terms(action_or_item):
    """Build a list of terms to match against agenda item titles.

    Accepts either an EntitlementAction ORM object or an extracted item dict.
    """
    case = None
    ordinance = None
    project = None

    if isinstance(action_or_item, dict):
        case = action_or_item.get("case_number")
        ordinance = action_or_item.get("ordinance_number")
        project = action_or_item.get("project_name")
    else:
        case = getattr(action_or_item, "case_number", None)
        ordinance = getattr(action_or_item, "ordinance_number", None)
        project = getattr(action_or_item, "project_name", None)

    terms = []
    if case:
        terms.append(case.strip())

    if ordinance:
        raw = ordinance.strip()
        bare = _ORD_PREFIX_RE.sub("", raw).strip()
        terms.append(bare)
        terms.append(f"Ordinance {bare}")
        terms.append(f"Ord {bare}")

    if not terms and project:
        terms.append(project.strip())

    return terms


def _title_matches(title_text, terms):
    """Check if any match term appears in the title text (case-insensitive)."""
    title_lower = title_text.lower()
    for term in terms:
        if term.lower() in title_lower:
            return True
    return False


def _full_url(href, base_domain):
    """Ensure a relative href becomes an absolute URL."""
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return base_domain + href
    return base_domain + "/" + href


def _get_base_domain(jurisdiction):
    """Extract scheme://host from the jurisdiction's agenda source URL."""
    base_url = jurisdiction.agenda_source_url or ""
    if not base_url:
        return None
    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def fetch_agenda_html(source_document, jurisdiction, cache=None):
    """Fetch and parse CivicPlus agenda HTML, with optional caching.

    Args:
        source_document: SourceDocument with a CivicPlus agenda source_url.
        jurisdiction: Jurisdiction instance.
        cache: Optional dict keyed by source_url → BeautifulSoup.

    Returns:
        (BeautifulSoup, base_domain) or (None, None) on failure.
    """
    if not source_document or not source_document.source_url:
        return None, None
    if not _CIVICPLUS_AGENDA_RE.search(source_document.source_url):
        return None, None

    base_domain = _get_base_domain(jurisdiction)
    if not base_domain:
        return None, None

    url = source_document.source_url
    if cache is not None and url in cache:
        return cache[url], base_domain

    html_url = url + "?html=true"
    if not html_url.startswith("http"):
        html_url = base_domain + html_url

    try:
        resp = requests.get(html_url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Failed to fetch agenda HTML %s: %s", html_url, e)
        if cache is not None:
            cache[url] = None
        return None, None

    soup = BeautifulSoup(resp.text, "html.parser")
    if cache is not None:
        cache[url] = soup
    return soup, base_domain


def _find_matching_item(soup, terms):
    """Walk agenda items and return the first div.item whose title matches."""
    for item_div in soup.select("div.item"):
        title_el = item_div.select_one(".title")
        if not title_el:
            continue
        if _title_matches(title_el.get_text(), terms):
            return item_div
    return None


def _parse_desc_fields(desc_div):
    """Parse structured label/value pairs from a CivicPlus desc div.

    Planning board agendas have structured HTML like:
        <p><strong><span>Label:</span></strong><span>Value</span></p>

    Returns dict of lowercase label → value string.
    """
    fields = {}
    for p_tag in desc_div.find_all("p"):
        strong = p_tag.find("strong")
        if not strong:
            continue
        label = strong.get_text().strip().rstrip(":")
        value_span = strong.find_next_sibling("span")
        if not value_span:
            all_spans = p_tag.find_all("span")
            value_span = all_spans[1] if len(all_spans) > 1 else None
        if not value_span:
            continue
        value = value_span.get_text().strip()
        if value:
            fields[label.lower()] = value
    return fields


# ── Public API ────────────────────────────────────────────────────────────


def resolve_packet_url(action, source_document, jurisdiction, cache=None):
    """Resolve the backup PDF URL for an action's agenda item.

    Returns:
        str URL or None.
    """
    if not jurisdiction or jurisdiction.agenda_platform != "civicplus":
        return None

    terms = _build_match_terms(action)
    if not terms:
        return None

    soup, base_domain = fetch_agenda_html(source_document, jurisdiction, cache)
    if not soup:
        return None

    item_div = _find_matching_item(soup, terms)
    if not item_div:
        return None

    file_link = item_div.select_one("a.file[href]")
    if not file_link:
        return None

    return _full_url(file_link["href"], base_domain)


def parse_acreage_from_html(action, source_document, jurisdiction, cache=None):
    """Extract acreage and lot count from CivicPlus agenda HTML description.

    Returns:
        (acreage: float|None, lot_count: int|None)
    """
    fields = parse_item_fields_from_html(action, source_document, jurisdiction, cache)
    if not fields:
        return None, None
    return fields.get("acreage"), fields.get("lot_count")


def parse_item_fields_from_html(item_or_action, source_document, jurisdiction, cache=None):
    """Extract all available structured fields from CivicPlus agenda HTML.

    Works for both ORM EntitlementAction objects and extracted item dicts.

    For planning board agendas, parses the structured desc div for:
        acreage, lot_count, applicant_name, address, parcel_ids

    For all CivicPlus agendas, parses acreage from the item title if present
    (e.g. "approximately 2.14 acres").

    Returns:
        dict of field_name → value, or empty dict if nothing found.
    """
    if not jurisdiction or jurisdiction.agenda_platform != "civicplus":
        return {}

    terms = _build_match_terms(item_or_action)
    if not terms:
        return {}

    soup, _ = fetch_agenda_html(source_document, jurisdiction, cache)
    if not soup:
        return {}

    item_div = _find_matching_item(soup, terms)
    if not item_div:
        return {}

    result = {}

    # Try structured desc fields (planning board agendas)
    desc_div = item_div.select_one(".desc")
    if desc_div:
        fields = _parse_desc_fields(desc_div)

        # Acreage
        for key in ("acreage (+/-)", "acreage", "property size"):
            if key in fields:
                try:
                    result["acreage"] = float(fields[key].replace(",", ""))
                except ValueError:
                    pass
                break

        # Lot count
        for key in ("lot count", "lots", "units", "number of lots"):
            if key in fields:
                try:
                    result["lot_count"] = int(fields[key].replace(",", ""))
                except ValueError:
                    pass
                break

        # Applicant
        if "applicant" in fields:
            result["applicant_name"] = fields["applicant"]

        # Address and parcel IDs from address/location field
        for key in ("address/location", "address", "subject property"):
            if key in fields:
                addr_text = fields[key]
                # Extract parcel ID if embedded: "310 EAST BEACH DRIVE E (Parcel ID #: 19536-000-000)"
                parcel_match = _PARCEL_ID_RE.search(addr_text)
                if parcel_match:
                    result["parcel_ids"] = [parcel_match.group(1)]
                    # Clean address by removing parcel portion
                    clean_addr = addr_text[:parcel_match.start()].strip().rstrip("(")
                    if clean_addr:
                        result["address"] = clean_addr
                else:
                    result["address"] = addr_text
                break

        # Owner
        if "owner" in fields:
            result["owner"] = fields["owner"]

    # Fallback: try to extract acreage from the title text
    if "acreage" not in result:
        title_el = item_div.select_one(".title")
        if title_el:
            title_match = _ACREAGE_IN_TITLE_RE.search(title_el.get_text())
            if title_match:
                try:
                    result["acreage"] = float(title_match.group(1).replace(",", ""))
                except ValueError:
                    pass

    return result


def merge_html_fields_into_items(items, source_document, jurisdiction, cache=None):
    """Merge CivicPlus HTML-parsed fields into LLM-extracted items.

    For each extracted item, looks up the matching agenda HTML item and fills
    in any null fields with HTML-sourced values.  Only fills fields that are
    null in the extracted item — never overwrites LLM-extracted data.

    Args:
        items: List of extracted item dicts (mutated in place).
        source_document: SourceDocument instance.
        jurisdiction: Jurisdiction instance.
        cache: Optional HTML cache dict.

    Returns:
        int count of items enriched (at least one field filled).
    """
    if not jurisdiction or jurisdiction.agenda_platform != "civicplus":
        return 0
    if not source_document or not source_document.source_url:
        return 0
    if not _CIVICPLUS_AGENDA_RE.search(source_document.source_url):
        return 0

    enriched = 0
    # Field mapping: html_key → item_key
    FIELD_MAP = {
        "acreage": "acreage",
        "lot_count": "lot_count",
        "applicant_name": "applicant_name",
        "address": "address",
        "parcel_ids": "parcel_ids",
    }

    for item in items:
        html_fields = parse_item_fields_from_html(item, source_document, jurisdiction, cache)
        if not html_fields:
            continue

        filled_any = False
        for html_key, item_key in FIELD_MAP.items():
            if html_key not in html_fields:
                continue
            current = item.get(item_key)
            # Only fill nulls / empty lists
            if current is None or current == [] or current == "":
                item[item_key] = html_fields[html_key]
                filled_any = True

        if filled_any:
            enriched += 1

    return enriched
