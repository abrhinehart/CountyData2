from pathlib import Path

import psycopg2
import psycopg2.extras


_UPSERT_SQL = """
INSERT INTO transactions (
    grantor, grantee, type, instrument, date,
    legal_desc, legal_raw, subdivision, subdivision_id, phase,
    lots, price, parsed_data, county, builder_id,
    grantor_builder_id, grantee_builder_id,
    grantor_land_banker_id, grantee_land_banker_id,
    review_flag, source_file
)
VALUES (
    %(grantor)s, %(grantee)s, %(type)s, %(instrument)s, %(date)s,
    %(legal_desc)s, %(legal_raw)s, %(subdivision)s, %(subdivision_id)s, %(phase)s,
    %(lots)s, %(price)s, %(parsed_data)s, %(county)s, %(builder_id)s,
    %(grantor_builder_id)s, %(grantee_builder_id)s,
    %(grantor_land_banker_id)s, %(grantee_land_banker_id)s,
    %(review_flag)s, %(source_file)s
)
ON CONFLICT (grantor_key, grantee_key, instrument_key, date, county_key)
DO UPDATE SET
    type                    = EXCLUDED.type,
    legal_desc              = EXCLUDED.legal_desc,
    legal_raw               = EXCLUDED.legal_raw,
    subdivision             = EXCLUDED.subdivision,
    subdivision_id          = EXCLUDED.subdivision_id,
    phase                   = EXCLUDED.phase,
    lots                    = EXCLUDED.lots,
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
RETURNING (xmax = 0) AS inserted
"""


def _prepare_db_row(row: dict) -> dict:
    prepared = dict(row)
    prepared['parsed_data'] = psycopg2.extras.Json(prepared.get('parsed_data') or {})
    return prepared


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
                if result and result[0]:
                    inserted += 1
                else:
                    updated += 1
            except Exception as e:
                conn.rollback()
                print(f"    Row error ({row.get('county', '?')}): {e}")
                errors += 1

    conn.commit()
    return inserted, updated, errors
