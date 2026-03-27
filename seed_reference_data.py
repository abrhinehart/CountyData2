"""
seed_reference_data.py - Load subdivision, builder, and land banker reference data from YAML into PostgreSQL.

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


def seed_named_alias_entities(conn, path_name: str, entity_table: str,
                              alias_table: str, alias_fk: str, label: str):
    path = REF_DIR / path_name
    if not path.exists():
        print(f'No {path_name} found - skipping.')
        return

    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or []

    inserted_entities = 0
    inserted_aliases = 0

    with conn.cursor() as cur:
        for entry in data:
            name = entry['canonical_name']
            aliases = entry.get('aliases', [name])

            cur.execute(f"""
                INSERT INTO {entity_table} (canonical_name)
                VALUES (%s)
                ON CONFLICT (canonical_name) DO NOTHING
                RETURNING id
            """, (name,))
            row = cur.fetchone()
            if row:
                entity_id = row[0]
                inserted_entities += 1
            else:
                cur.execute(f"SELECT id FROM {entity_table} WHERE canonical_name = %s", (name,))
                entity_id = cur.fetchone()[0]

            for alias in aliases:
                cur.execute(f"""
                    INSERT INTO {alias_table} ({alias_fk}, alias)
                    VALUES (%s, %s)
                    ON CONFLICT (alias) DO NOTHING
                """, (entity_id, alias))
                inserted_aliases += cur.rowcount

    conn.commit()
    print(f'{label}: {inserted_entities} new, {inserted_aliases} new aliases.')


def seed_builders(conn):
    seed_named_alias_entities(
        conn,
        path_name='builders.yaml',
        entity_table='builders',
        alias_table='builder_aliases',
        alias_fk='builder_id',
        label='Builders',
    )


def seed_land_bankers(conn):
    seed_named_alias_entities(
        conn,
        path_name='land_bankers.yaml',
        entity_table='land_bankers',
        alias_table='land_banker_aliases',
        alias_fk='land_banker_id',
        label='Land bankers',
    )


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
