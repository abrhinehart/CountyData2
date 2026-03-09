"""
003_backfill.py — One-time migration to populate new lookup columns on existing data.

Steps:
  1. Populate legal_raw from existing legal_desc (imperfect but non-null)
  2. Match existing legal_desc against SubdivisionMatcher → fill subdivision_id
  3. Match existing grantor against BuilderMatcher → fill builder_id, update grantor
  4. Set review_flag = TRUE on all backfilled rows

Usage:
    python -m migrations.003_backfill
    python migrations/003_backfill.py
"""

import sys
from pathlib import Path

# Allow running as script or module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from config import DATABASE_URL
from utils.lookup import SubdivisionMatcher, BuilderMatcher


def backfill_legal_raw(conn):
    """Populate legal_raw from legal_desc for rows where legal_raw is NULL."""
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
    """Match existing legal_desc against subdivision aliases."""
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


def backfill_builders(conn, matcher):
    """Match existing grantor against builder aliases."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, grantor
            FROM transactions
            WHERE builder_id IS NULL AND grantor IS NOT NULL
        """)
        rows = cur.fetchall()

    matched = 0
    with conn.cursor() as cur:
        for txn_id, grantor in rows:
            builder_id, canonical = matcher.match(grantor)
            if builder_id is not None:
                cur.execute("""
                    UPDATE transactions
                    SET builder_id = %s,
                        grantor = %s,
                        review_flag = TRUE
                    WHERE id = %s
                """, (builder_id, canonical, txn_id))
                matched += 1

    conn.commit()
    print(f"  builder_id backfilled: {matched} / {len(rows)} rows matched")
    return matched


def main():
    print("Backfill migration: populating new lookup columns...")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        backfill_legal_raw(conn)

        sub_matcher = SubdivisionMatcher(conn)
        builder_matcher = BuilderMatcher(conn)

        backfill_subdivisions(conn, sub_matcher)
        backfill_builders(conn, builder_matcher)
    finally:
        conn.close()
    print("Done.")


if __name__ == '__main__':
    main()
