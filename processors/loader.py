from pathlib import Path

import psycopg2
import psycopg2.extras


_UPSERT_SQL = """
INSERT INTO transactions (
    grantor, grantee, type, instrument, date,
    export_legal_desc, export_legal_raw, deed_locator, deed_legal_desc, deed_legal_parsed,
    subdivision, subdivision_id, phase, inventory_category,
    lots, acres, acres_source, price, parsed_data, county, builder_id,
    grantor_builder_id, grantee_builder_id,
    grantor_land_banker_id, grantee_land_banker_id,
    review_flag, source_file
)
VALUES (
    %(grantor)s, %(grantee)s, %(type)s, %(instrument)s, %(date)s,
    %(export_legal_desc)s, %(export_legal_raw)s, %(deed_locator)s, %(deed_legal_desc)s, %(deed_legal_parsed)s,
    %(subdivision)s, %(subdivision_id)s, %(phase)s, %(inventory_category)s,
    %(lots)s, %(acres)s, %(acres_source)s, %(price)s, %(parsed_data)s, %(county)s, %(builder_id)s,
    %(grantor_builder_id)s, %(grantee_builder_id)s,
    %(grantor_land_banker_id)s, %(grantee_land_banker_id)s,
    %(review_flag)s, %(source_file)s
)
ON CONFLICT (grantor_key, grantee_key, instrument_key, date, county_key)
DO UPDATE SET
    type                    = EXCLUDED.type,
    export_legal_desc       = EXCLUDED.export_legal_desc,
    export_legal_raw        = EXCLUDED.export_legal_raw,
    deed_locator            = EXCLUDED.deed_locator,
    deed_legal_desc         = EXCLUDED.deed_legal_desc,
    deed_legal_parsed       = EXCLUDED.deed_legal_parsed,
    subdivision             = EXCLUDED.subdivision,
    subdivision_id          = EXCLUDED.subdivision_id,
    phase                   = EXCLUDED.phase,
    inventory_category      = EXCLUDED.inventory_category,
    lots                    = EXCLUDED.lots,
    acres                   = EXCLUDED.acres,
    acres_source            = EXCLUDED.acres_source,
    price                   = EXCLUDED.price,
    parsed_data             = EXCLUDED.parsed_data,
    builder_id              = EXCLUDED.builder_id,
    grantor_builder_id      = EXCLUDED.grantor_builder_id,
    grantee_builder_id      = EXCLUDED.grantee_builder_id,
    grantor_land_banker_id  = EXCLUDED.grantor_land_banker_id,
    grantee_land_banker_id  = EXCLUDED.grantee_land_banker_id,
    review_flag             = EXCLUDED.review_flag,
    source_file             = EXCLUDED.source_file,
    updated_at              = NOW()
RETURNING id, (xmax = 0) AS inserted
"""

_DELETE_SEGMENTS_SQL = """
DELETE FROM transaction_segments
WHERE transaction_id = %s
"""

_INSERT_SEGMENTS_SQL = """
INSERT INTO transaction_segments (
    transaction_id, segment_index, county, subdivision_lookup_text,
    raw_subdivision, subdivision, subdivision_id, phase_raw, phase,
    inventory_category, phase_confirmed, segment_review_reasons, segment_data
)
VALUES %s
"""


def _prepare_db_row(row: dict) -> dict:
    prepared = dict(row)
    prepared['parsed_data'] = psycopg2.extras.Json(prepared.get('parsed_data') or {})
    prepared['deed_locator'] = psycopg2.extras.Json(prepared.get('deed_locator') or {})
    prepared['deed_legal_parsed'] = psycopg2.extras.Json(prepared.get('deed_legal_parsed') or {})
    return prepared


def _prepare_segment_rows(transaction_id: int, row: dict) -> list[tuple]:
    segment_rows = []
    for segment in row.get('transaction_segments') or []:
        segment_rows.append((
            transaction_id,
            segment.get('segment_index'),
            segment.get('county') or row.get('county'),
            segment.get('subdivision_lookup_text'),
            segment.get('raw_subdivision'),
            segment.get('subdivision'),
            segment.get('subdivision_id'),
            segment.get('phase_raw'),
            segment.get('phase'),
            segment.get('inventory_category'),
            segment.get('phase_confirmed'),
            list(segment.get('review_reasons') or []),
            psycopg2.extras.Json(segment.get('segment_data') or {}),
        ))
    return segment_rows


def _replace_transaction_segments(cur, transaction_id: int, row: dict) -> None:
    cur.execute(_DELETE_SEGMENTS_SQL, (transaction_id,))
    segment_rows = _prepare_segment_rows(transaction_id, row)
    if not segment_rows:
        return

    psycopg2.extras.execute_values(
        cur,
        _INSERT_SEGMENTS_SQL,
        segment_rows,
        template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
    )


def upsert_rows(rows: list[dict], source_file: Path, conn) -> tuple[int, int, int]:
    """
    Bulk-upsert rows into the transactions table.
    Returns (inserted_count, updated_count, error_count).
    """
    inserted = updated = errors = 0

    with conn.cursor() as cur:
        for row in rows:
            row['source_file'] = str(source_file)
            try:
                cur.execute(_UPSERT_SQL, _prepare_db_row(row))
                result = cur.fetchone()
                transaction_id = None
                inserted_row = False
                if result:
                    transaction_id = result[0]
                    inserted_row = bool(result[1])

                if transaction_id is not None:
                    _replace_transaction_segments(cur, transaction_id, row)

                if inserted_row:
                    inserted += 1
                else:
                    updated += 1
            except Exception as e:
                conn.rollback()
                print(f"    Row error ({row.get('county', '?')}): {e}")
                errors += 1

    conn.commit()
    return inserted, updated, errors
