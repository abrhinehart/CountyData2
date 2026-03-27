"""
003_backfill.py - One-time migration to populate lookup columns on existing data.

Steps:
  1. Populate legal_raw from existing legal_desc (imperfect but non-null)
  2. Match existing legal_desc against SubdivisionMatcher -> fill subdivision_id
  3. Match existing grantor/grantee against builder and land banker aliases
  4. Populate side-specific party IDs and compatibility builder_id

Usage:
    python -m migrations.003_backfill
    python migrations/003_backfill.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2

from config import DATABASE_URL
from utils.lookup import BuilderMatcher, LandBankerMatcher, SubdivisionMatcher
from utils.transaction_utils import classify_transaction_type


def backfill_legal_raw(conn):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE transactions
            SET legal_raw = legal_desc
            WHERE legal_raw IS NULL AND legal_desc IS NOT NULL
        """)
        count = cur.rowcount
    conn.commit()
    print(f"  legal_raw backfilled: {count} rows")
    return count


def backfill_subdivisions(conn, matcher):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, legal_desc, county
            FROM transactions
            WHERE subdivision_id IS NULL AND legal_desc IS NOT NULL
        """)
        rows = cur.fetchall()

    matched = 0
    with conn.cursor() as cur:
        for txn_id, legal_desc, county in rows:
            sub_id, canonical, phase = matcher.match(legal_desc, county)
            if sub_id is not None:
                cur.execute("""
                    UPDATE transactions
                    SET subdivision_id = %s,
                        subdivision = %s,
                        phase = COALESCE(phase, %s),
                        review_flag = TRUE
                    WHERE id = %s
                """, (sub_id, canonical, phase, txn_id))
                matched += 1

    conn.commit()
    print(f"  subdivision_id backfilled: {matched} / {len(rows)} rows matched")
    return matched


def backfill_party_entities(conn, builder_matcher, land_banker_matcher):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, grantor, grantee
            FROM transactions
            WHERE
                grantor_builder_id IS NULL
                OR grantee_builder_id IS NULL
                OR grantor_land_banker_id IS NULL
                OR grantee_land_banker_id IS NULL
        """)
        rows = cur.fetchall()

    matched = 0
    with conn.cursor() as cur:
        for txn_id, grantor, grantee in rows:
            grantor_builder_id, _ = builder_matcher.match(grantor)
            grantee_builder_id, _ = builder_matcher.match(grantee)
            grantor_land_banker_id, _ = land_banker_matcher.match(grantor)
            grantee_land_banker_id, _ = land_banker_matcher.match(grantee)
            builder_id = grantee_builder_id or grantor_builder_id

            if any((grantor_builder_id, grantee_builder_id, grantor_land_banker_id, grantee_land_banker_id)):
                tx_type = classify_transaction_type(
                    grantor_builder_id,
                    grantee_builder_id,
                    grantor_land_banker_id,
                    grantee_land_banker_id,
                )
                cur.execute("""
                    UPDATE transactions
                    SET grantor_builder_id = %s,
                        grantee_builder_id = %s,
                        grantor_land_banker_id = %s,
                        grantee_land_banker_id = %s,
                        builder_id = %s,
                        type = %s,
                        review_flag = TRUE
                    WHERE id = %s
                """, (
                    grantor_builder_id,
                    grantee_builder_id,
                    grantor_land_banker_id,
                    grantee_land_banker_id,
                    builder_id,
                    tx_type,
                    txn_id,
                ))
                matched += 1

    conn.commit()
    print(f"  party entities backfilled: {matched} / {len(rows)} rows matched")
    return matched


def main():
    print("Backfill migration: populating lookup columns...")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        backfill_legal_raw(conn)

        sub_matcher = SubdivisionMatcher(conn)
        builder_matcher = BuilderMatcher(conn)
        land_banker_matcher = LandBankerMatcher(conn)

        backfill_subdivisions(conn, sub_matcher)
        backfill_party_entities(conn, builder_matcher, land_banker_matcher)
    finally:
        conn.close()
    print("Done.")


if __name__ == '__main__':
    main()
