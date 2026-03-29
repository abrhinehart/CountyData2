"""
apply_migrations.py - Apply additive SQL migrations in order.

Usage:
    python apply_migrations.py
    python apply_migrations.py --list
"""

from __future__ import annotations

import argparse
from pathlib import Path

import psycopg2

from config import DATABASE_URL


MIGRATIONS_DIR = Path(__file__).parent / 'migrations'


def get_sql_migrations() -> list[Path]:
    return sorted(
        path
        for path in MIGRATIONS_DIR.glob('[0-9][0-9][0-9]_*.sql')
        if path.is_file()
    )


def apply_sql_migration(conn, path: Path) -> None:
    sql = path.read_text(encoding='utf-8')
    if not sql.strip():
        print(f'Skipping {path.name} (empty).')
        return

    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f'Applied {path.name}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Apply SQL migrations in order')
    parser.add_argument('--list', action='store_true', help='List SQL migrations and exit')
    args = parser.parse_args()

    migrations = get_sql_migrations()
    if args.list:
        for path in migrations:
            print(path.name)
        return

    if not migrations:
        print('No SQL migrations found.')
        return

    conn = psycopg2.connect(DATABASE_URL)
    try:
        for path in migrations:
            try:
                apply_sql_migration(conn, path)
            except Exception:
                conn.rollback()
                print(f'Failed while applying {path.name}.')
                raise
    finally:
        conn.close()

    print(f'Done. Applied {len(migrations)} SQL migrations.')


if __name__ == '__main__':
    main()
