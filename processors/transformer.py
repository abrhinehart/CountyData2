import pandas as pd

from utils.county_utils import normalize_county_key
from utils.date_utils import parse_date
from utils.text_cleaning import (
    split_parties,
    before_first_delimiter,
    before_first_newline,
    extract_phase,
    remove_phase_from_text,
    clean_subdivision,
    remove_santarosa_unit,
    fix_phase_typos,
    remove_after_parcel,
    remove_after_section,
    remove_unrec,
)
from utils.transaction_utils import classify_transaction_type


def _resolve_party(raw, delimiters, builder_matcher, land_banker_matcher):
    """
    Split a multi-party field, check each name against builder and land banker
    matchers, and return (display_name, builder_id, land_banker_id).

    Keep the first source party for storage so reruns do not change the dedup
    key when aliases are added later. Match IDs can come from any party in the
    field without rewriting the stored display text.
    """
    parties = split_parties(raw, delimiters)
    if not parties:
        return '', None, None

    builder_id = None
    land_banker_id = None

    for name in parties:
        if builder_matcher and builder_id is None:
            builder_id, _canonical = builder_matcher.match(name)
        if land_banker_matcher and land_banker_id is None:
            land_banker_id, _canonical = land_banker_matcher.match(name)
        if builder_id is not None and land_banker_id is not None:
            break

    return parties[0], builder_id, land_banker_id


def transform_row(row: pd.Series, county: str, config: dict,
                  sub_matcher=None, builder_matcher=None,
                  land_banker_matcher=None) -> dict | None:
    """
    Transform a raw source row into a clean dict ready for DB insert.
    Returns None if the row should be skipped (missing grantor).
    """
    cols = config['column_mapping']
    delimiters = config.get('delimiters', [])
    county_key = normalize_county_key(county)

    # --- Grantor / Grantee (multi-party with entity matching) ---
    grantor_raw = row.get(cols.get('grantor', ''), pd.NA)
    if pd.isna(grantor_raw) or not str(grantor_raw).strip():
        return None

    grantor, grantor_builder_id, grantor_land_banker_id = _resolve_party(
        grantor_raw, delimiters, builder_matcher, land_banker_matcher
    )

    grantee_raw = row.get(cols.get('grantee', ''), pd.NA)
    grantee, grantee_builder_id, grantee_land_banker_id = _resolve_party(
        grantee_raw, delimiters, builder_matcher, land_banker_matcher
    )

    # Keep legacy builder_id populated for compatibility, preferring the buyer side.
    builder_id = grantee_builder_id or grantor_builder_id

    # --- County-specific party swaps ---
    if county_key == 'MARION':
        star_col = cols.get('star', 'Star')
        if star_col in row and str(row[star_col]).strip() != '*':
            grantor, grantee = grantee, grantor
            grantor_builder_id, grantee_builder_id = grantee_builder_id, grantor_builder_id
            grantor_land_banker_id, grantee_land_banker_id = grantee_land_banker_id, grantor_land_banker_id

    elif county_key == 'SANTAROSA':
        party_type_col = cols.get('party_type', 'Party Type')
        if party_type_col in row:
            if 'to' in str(row[party_type_col]).strip().lower():
                grantor, grantee = grantee, grantor
                grantor_builder_id, grantee_builder_id = grantee_builder_id, grantor_builder_id
                grantor_land_banker_id, grantee_land_banker_id = grantee_land_banker_id, grantor_land_banker_id

    # --- Legal description (dual output: legal_raw + legal_desc) ---
    legal_src = row.get(cols.get('legal', ''), pd.NA)
    legal = str(legal_src).replace('\n', ' ').strip() if pd.notna(legal_src) else ''

    if county_key == 'WALTON':
        legal = legal.replace('Legal ', '').strip()
    elif county_key == 'HERNANDO':
        legal = legal.replace('L Blk Un Sub', '').replace('S T R', '').strip()
        sub_col = cols.get('sub', 'Subdivision')
        if sub_col in row and pd.notna(row[sub_col]):
            row = row.copy()
            row[sub_col] = str(row[sub_col]).replace('legalfield_', '').strip()
    elif county_key == 'SANTAROSA':
        legal = remove_unrec(legal)
    elif county_key == 'OKALOOSA':
        legal = remove_after_parcel(legal)
        legal = remove_after_section(legal)

    legal_raw = legal or None
    legal_desc = legal[:75].strip() if legal else None

    if county_key == 'HERNANDO':
        sub_raw = row.get(cols.get('sub', ''), pd.NA)
        extract_text = str(sub_raw).replace('\n', ' ').strip() if pd.notna(sub_raw) else legal
    else:
        extract_text = legal

    # --- Subdivision and phase (lookup-first, regex fallback) ---
    phase_keywords = config.get('phase_keywords', [])
    review_flag = False
    subdivision_id = None
    subdivision = None
    phase = None

    if sub_matcher:
        subdivision_id, subdivision, phase = sub_matcher.match(
            extract_text, county, phase_keywords
        )

    if subdivision_id is not None:
        if phase is None:
            phase = fix_phase_typos(extract_phase(extract_text, phase_keywords))
            if phase:
                review_flag = True
    else:
        review_flag = True
        phase = fix_phase_typos(extract_phase(extract_text, phase_keywords))
        subdivision = clean_subdivision(extract_text, phase_keywords)

        if county_key in {'SANTAROSA', 'CITRUS'}:
            subdivision = remove_santarosa_unit(subdivision)

        subdivision = subdivision[:75].strip() if subdivision else None

    instrument = str(row.get(cols.get('instrument', ''), '')).strip()
    date = parse_date(row.get(cols.get('date', ''), pd.NA))

    price_raw = row.get(cols.get('price', ''), '')
    try:
        price = float(str(price_raw).replace(',', '').strip()) if str(price_raw).strip() else None
    except (ValueError, TypeError):
        price = None

    lots_col = cols.get('lots', '')
    lots_raw = row.get(lots_col, '') if lots_col else ''
    try:
        lots = int(float(str(lots_raw).strip())) if str(lots_raw).strip() else 1
    except (ValueError, TypeError):
        lots = 1

    trans_type = classify_transaction_type(
        grantor_builder_id,
        grantee_builder_id,
        grantor_land_banker_id,
        grantee_land_banker_id,
    )

    return {
        'grantor':                 grantor,
        'grantee':                 grantee or None,
        'type':                    trans_type,
        'instrument':              instrument or None,
        'date':                    date,
        'legal_desc':              legal_desc,
        'legal_raw':               legal_raw,
        'subdivision':             subdivision or None,
        'subdivision_id':          subdivision_id,
        'phase':                   phase or None,
        'lots':                    lots,
        'price':                   price,
        'county':                  county,
        'builder_id':              builder_id,
        'grantor_builder_id':      grantor_builder_id,
        'grantee_builder_id':      grantee_builder_id,
        'grantor_land_banker_id':  grantor_land_banker_id,
        'grantee_land_banker_id':  grantee_land_banker_id,
        'review_flag':             review_flag,
    }
