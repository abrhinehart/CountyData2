"""
seed_reference_data.py - Load subdivision, builder, and land banker reference data from YAML into PostgreSQL.

Idempotent: safe to run multiple times (uses ON CONFLICT).

Post-unification: land_bankers are now stored in the builders table with a type column.

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
        print('No subdivisions.yaml found - skipping.')
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
                    INSERT INTO subdivisions (canonical_name, county, phases, classification)
                    VALUES (%s, %s, %s, 'active_development')
                    ON CONFLICT (canonical_name, county) DO UPDATE
                        SET phases = EXCLUDED.phases,
                            classification = 'active_development'
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

                # Also seed phases into the phases table
                for phase_name in phases:
                    cur.execute("""
                        INSERT INTO phases (subdivision_id, name)
                        VALUES (%s, %s)
                        ON CONFLICT (subdivision_id, name) DO NOTHING
                    """, (sub_id, str(phase_name)))

    conn.commit()
    print(f'Subdivisions: {inserted_subs} upserted, {inserted_aliases} new aliases.')


def seed_builders(conn):
    """Seed builders from builders.yaml (type='builder')."""
    path = REF_DIR / 'builders.yaml'
    if not path.exists():
        print('No builders.yaml found - skipping.')
        return

    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or []

    inserted_entities = 0
    inserted_aliases = 0

    with conn.cursor() as cur:
        for entry in data:
            name = entry['canonical_name']
            aliases = entry.get('aliases', [name])

            cur.execute("""
                INSERT INTO builders (canonical_name, type, scope, is_active)
                VALUES (%s, 'builder', 'national', true)
                ON CONFLICT (canonical_name) DO NOTHING
                RETURNING id
            """, (name,))
            row = cur.fetchone()
            if row:
                entity_id = row[0]
                inserted_entities += 1
            else:
                cur.execute("SELECT id FROM builders WHERE canonical_name = %s", (name,))
                entity_id = cur.fetchone()[0]

            for alias in aliases:
                cur.execute("""
                    INSERT INTO builder_aliases (builder_id, alias)
                    VALUES (%s, %s)
                    ON CONFLICT (alias) DO NOTHING
                """, (entity_id, alias))
                inserted_aliases += cur.rowcount

    conn.commit()
    print(f'Builders: {inserted_entities} new, {inserted_aliases} new aliases.')


def seed_land_bankers(conn):
    """Seed land bankers into the unified builders table with appropriate type."""
    path = REF_DIR / 'land_bankers.yaml'
    if not path.exists():
        print('No land_bankers.yaml found - skipping.')
        return

    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or []

    inserted_entities = 0
    inserted_aliases = 0

    with conn.cursor() as cur:
        for entry in data:
            name = entry['canonical_name']
            category = entry.get('category', 'land_banker')
            aliases = entry.get('aliases', [name])

            cur.execute("""
                INSERT INTO builders (canonical_name, type, scope, is_active)
                VALUES (%s, %s, 'national', true)
                ON CONFLICT (canonical_name) DO UPDATE
                    SET type = EXCLUDED.type
                RETURNING id
            """, (name, category))
            row = cur.fetchone()
            if row:
                entity_id = row[0]
                inserted_entities += 1
            else:
                cur.execute("SELECT id FROM builders WHERE canonical_name = %s", (name,))
                entity_id = cur.fetchone()[0]

            for alias in aliases:
                cur.execute("""
                    INSERT INTO builder_aliases (builder_id, alias)
                    VALUES (%s, %s)
                    ON CONFLICT (alias) DO NOTHING
                """, (entity_id, alias))
                inserted_aliases += cur.rowcount

    conn.commit()
    print(f'Land bankers: {inserted_entities} upserted, {inserted_aliases} new aliases.')


def main():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        seed_subdivisions(conn)
        seed_builders(conn)
        seed_land_bankers(conn)
    finally:
        conn.close()
    print('Done.')


if __name__ == '__main__':
    main()
