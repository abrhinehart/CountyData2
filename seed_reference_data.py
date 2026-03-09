"""
seed_reference_data.py — Load subdivision and builder reference data from YAML into PostgreSQL.

Idempotent: safe to run multiple times (uses ON CONFLICT).

Usage:
    python seed_reference_data.py
"""

from pathlib import Path

import psycopg2
import yaml

from config import DATABASE_URL

REF_DIR = Path(__file__).parent / 'reference_data'


def seed_subdivisions(conn):
    path = REF_DIR / 'subdivisions.yaml'
    if not path.exists():
        print('No subdivisions.yaml found — skipping.')
        return

    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    inserted_subs = 0
    inserted_aliases = 0

    with conn.cursor() as cur:
        for county, entries in data.items():
            if not entries:
                continue
            for entry in entries:
                name = entry['canonical_name']
                phases = entry.get('phases', [])
                aliases = entry.get('aliases', [name])

                cur.execute("""
                    INSERT INTO subdivisions (canonical_name, county, phases)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (canonical_name, county) DO UPDATE
                        SET phases = EXCLUDED.phases
                    RETURNING id
                """, (name, county, phases))
                sub_id = cur.fetchone()[0]
                inserted_subs += 1

                for alias in aliases:
                    cur.execute("""
                        INSERT INTO subdivision_aliases (subdivision_id, alias)
                        VALUES (%s, %s)
                        ON CONFLICT (alias, subdivision_id) DO NOTHING
                    """, (sub_id, alias))
                    inserted_aliases += cur.rowcount

    conn.commit()
    print(f'Subdivisions: {inserted_subs} upserted, {inserted_aliases} new aliases.')


def seed_builders(conn):
    path = REF_DIR / 'builders.yaml'
    if not path.exists():
        print('No builders.yaml found — skipping.')
        return

    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or []

    inserted_builders = 0
    inserted_aliases = 0

    with conn.cursor() as cur:
        for entry in data:
            name = entry['canonical_name']
            aliases = entry.get('aliases', [name])

            cur.execute("""
                INSERT INTO builders (canonical_name)
                VALUES (%s)
                ON CONFLICT (canonical_name) DO NOTHING
                RETURNING id
            """, (name,))
            row = cur.fetchone()
            if row:
                builder_id = row[0]
                inserted_builders += 1
            else:
                cur.execute("SELECT id FROM builders WHERE canonical_name = %s", (name,))
                builder_id = cur.fetchone()[0]

            for alias in aliases:
                cur.execute("""
                    INSERT INTO builder_aliases (builder_id, alias)
                    VALUES (%s, %s)
                    ON CONFLICT (alias) DO NOTHING
                """, (builder_id, alias))
                inserted_aliases += cur.rowcount

    conn.commit()
    print(f'Builders: {inserted_builders} new, {inserted_aliases} new aliases.')


def main():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        seed_subdivisions(conn)
        seed_builders(conn)
    finally:
        conn.close()
    print('Done.')


if __name__ == '__main__':
    main()
