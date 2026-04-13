"""
004_backend_cleanup.py — Schema additions and data cleanup for backend issues.

Steps:
  1. Add `source` column to builders table (default 'manual')
  2. Mark auto-inserted builders (no aliases, no county links) as source='permit_auto', is_active=FALSE
  3. Mark curated builders as source='seed'
  4. Add `is_relevant` column to subdivisions table (default FALSE)
  5. Backfill is_relevant=TRUE for subdivisions with real activity
  6. Deactivate noise subdivisions (no parcels, no actions, no transactions, no permits)
  7. Add `is_active` column to cr_jurisdiction_config (default TRUE)
  8. Deactivate BOA jurisdiction configs (commission_type='board_of_adjustment')

Usage:
    python -m migrations.004_backend_cleanup
    python -m migrations.004_backend_cleanup --dry-run
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2

from config import DATABASE_URL

DRY_RUN = "--dry-run" in sys.argv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _col_exists(cur, table, column):
    cur.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    return cur.fetchone() is not None


# ---------------------------------------------------------------------------
# Builder cleanup
# ---------------------------------------------------------------------------

def add_builder_source_column(conn):
    """Add source column to builders if it doesn't exist."""
    with conn.cursor() as cur:
        if _col_exists(cur, "builders", "source"):
            print("  builders.source already exists, skipping")
            return 0
        if DRY_RUN:
            print("  [DRY RUN] would add builders.source column")
            return 0
        cur.execute("""
            ALTER TABLE builders
            ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'manual'
        """)
    conn.commit()
    print("  builders.source column added")
    return 1


def mark_auto_inserted_builders(conn):
    """Mark builders with no aliases and no county links as permit_auto + inactive."""
    source_exists = False
    with conn.cursor() as cur:
        source_exists = _col_exists(cur, "builders", "source")

    with conn.cursor() as cur:
        # Preview what will be affected (use source filter only if column exists)
        source_clause = "AND source = 'manual'" if source_exists else ""
        cur.execute(f"""
            SELECT id, canonical_name FROM builders
            WHERE is_active = TRUE
              {source_clause}
              AND NOT EXISTS (
                  SELECT 1 FROM builder_aliases WHERE builder_aliases.builder_id = builders.id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM builder_counties WHERE builder_counties.builder_id = builders.id
              )
            ORDER BY canonical_name
        """)
        rows = cur.fetchall()

    count = len(rows)
    if count == 0:
        print("  No auto-inserted builders to deactivate")
        return 0

    print(f"  {count} builders identified as permit-auto-inserted (no aliases, no county links)")
    if count <= 20:
        for r in rows:
            print(f"    - [{r[0]}] {r[1]}")
    else:
        for r in rows[:5]:
            print(f"    - [{r[0]}] {r[1]}")
        print(f"    ... and {count - 5} more")

    if DRY_RUN:
        print(f"  [DRY RUN] would deactivate {count} builders")
        return count

    with conn.cursor() as cur:
        cur.execute("""
            UPDATE builders
            SET source = 'permit_auto', is_active = FALSE
            WHERE source = 'manual'
              AND NOT EXISTS (
                  SELECT 1 FROM builder_aliases WHERE builder_aliases.builder_id = builders.id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM builder_counties WHERE builder_counties.builder_id = builders.id
              )
        """)
        updated = cur.rowcount
    conn.commit()
    print(f"  {updated} auto-inserted builders marked as permit_auto + deactivated")
    return updated


def mark_seed_builders(conn):
    """Mark builders that have aliases or county links as seed-origin."""
    source_exists = False
    with conn.cursor() as cur:
        source_exists = _col_exists(cur, "builders", "source")

    with conn.cursor() as cur:
        source_clause = "AND source = 'manual'" if source_exists else "AND is_active = TRUE"
        if DRY_RUN:
            cur.execute(f"""
                SELECT count(*) FROM builders
                WHERE 1=1 {source_clause}
                  AND (
                      EXISTS (SELECT 1 FROM builder_aliases WHERE builder_aliases.builder_id = builders.id)
                      OR EXISTS (SELECT 1 FROM builder_counties WHERE builder_counties.builder_id = builders.id)
                  )
            """)
            count = cur.fetchone()[0]
            print(f"  [DRY RUN] would mark {count} builders as source='seed'")
            return count

        cur.execute(f"""
            UPDATE builders
            SET source = 'seed'
            WHERE 1=1 {source_clause}
              AND (
                  EXISTS (SELECT 1 FROM builder_aliases WHERE builder_aliases.builder_id = builders.id)
                  OR EXISTS (SELECT 1 FROM builder_counties WHERE builder_counties.builder_id = builders.id)
              )
        """)
        count = cur.rowcount
    conn.commit()
    print(f"  {count} curated builders marked as seed")
    return count


# ---------------------------------------------------------------------------
# Subdivision cleanup
# ---------------------------------------------------------------------------

def add_subdivision_is_relevant(conn):
    """Add is_relevant column to subdivisions if it doesn't exist."""
    with conn.cursor() as cur:
        if _col_exists(cur, "subdivisions", "is_relevant"):
            print("  subdivisions.is_relevant already exists, skipping")
            return 0
        if DRY_RUN:
            print("  [DRY RUN] would add subdivisions.is_relevant column")
            return 0
        cur.execute("""
            ALTER TABLE subdivisions
            ADD COLUMN is_relevant BOOLEAN DEFAULT FALSE
        """)
    conn.commit()
    print("  subdivisions.is_relevant column added")
    return 1


def backfill_subdivision_relevance(conn):
    """Set is_relevant=TRUE for subdivisions with real activity from any module."""
    with conn.cursor() as cur:
        if DRY_RUN:
            # Count how many would be marked relevant by each source
            cur.execute("""SELECT count(DISTINCT subdivision_id) FROM parcels
                WHERE subdivision_id IS NOT NULL AND builder_id IS NOT NULL AND is_active = TRUE""")
            p = cur.fetchone()[0]
            cur.execute("""SELECT count(DISTINCT subdivision_id) FROM cr_entitlement_actions
                WHERE subdivision_id IS NOT NULL""")
            a = cur.fetchone()[0]
            cur.execute("""SELECT count(DISTINCT subdivision_id) FROM transactions
                WHERE subdivision_id IS NOT NULL AND date >= CURRENT_DATE - INTERVAL '120 days'""")
            t = cur.fetchone()[0]
            cur.execute("""SELECT count(DISTINCT subdivision_id) FROM pt_permits
                WHERE subdivision_id IS NOT NULL""")
            pp = cur.fetchone()[0]
            # Count subdivisions with seed aliases
            cur.execute("""SELECT count(DISTINCT subdivision_id) FROM subdivision_aliases""")
            sa = cur.fetchone()[0]
            print(f"  [DRY RUN] would mark relevant: {p} (parcels) + {a} (CR actions) + {t} (recent txns) + {pp} (permits) + {sa} (have aliases)")
            return 0

        # Subdivisions with active builder parcels
        cur.execute("""
            UPDATE subdivisions SET is_relevant = TRUE
            WHERE id IN (
                SELECT DISTINCT subdivision_id FROM parcels
                WHERE subdivision_id IS NOT NULL AND builder_id IS NOT NULL AND is_active = TRUE
            )
        """)
        parcel_count = cur.rowcount

        # Subdivisions with entitlement actions
        cur.execute("""
            UPDATE subdivisions SET is_relevant = TRUE
            WHERE is_relevant = FALSE AND id IN (
                SELECT DISTINCT subdivision_id FROM cr_entitlement_actions
                WHERE subdivision_id IS NOT NULL
            )
        """)
        action_count = cur.rowcount

        # Subdivisions with recent transactions (120-day window)
        cur.execute("""
            UPDATE subdivisions SET is_relevant = TRUE
            WHERE is_relevant = FALSE AND id IN (
                SELECT DISTINCT subdivision_id FROM transactions
                WHERE subdivision_id IS NOT NULL AND date >= CURRENT_DATE - INTERVAL '120 days'
            )
        """)
        txn_count = cur.rowcount

        # Subdivisions with permits linked
        cur.execute("""
            UPDATE subdivisions SET is_relevant = TRUE
            WHERE is_relevant = FALSE AND id IN (
                SELECT DISTINCT subdivision_id FROM pt_permits
                WHERE subdivision_id IS NOT NULL
            )
        """)
        permit_count = cur.rowcount

        # Subdivisions with curated aliases (from seed data)
        cur.execute("""
            UPDATE subdivisions SET is_relevant = TRUE
            WHERE is_relevant = FALSE AND id IN (
                SELECT DISTINCT subdivision_id FROM subdivision_aliases
            )
        """)
        alias_count = cur.rowcount

    conn.commit()
    print(f"  is_relevant=TRUE: {parcel_count} (parcels) + {action_count} (CR actions) "
          f"+ {txn_count} (recent txns) + {permit_count} (permits) + {alias_count} (have aliases)")
    return parcel_count + action_count + txn_count + permit_count + alias_count


def deactivate_noise_subdivisions(conn):
    """Deactivate subdivisions with no real activity from any source.

    A subdivision is noise if it has:
    - No parcels referencing it
    - No entitlement actions referencing it
    - No transactions referencing it (ever, not just recent)
    - No permits referencing it
    - No subdivision_aliases (i.e., not from seed data)
    - is_relevant = FALSE (if column exists)
    """
    relevant_exists = False
    with conn.cursor() as cur:
        relevant_exists = _col_exists(cur, "subdivisions", "is_relevant")

    relevant_clause = "AND is_relevant = FALSE" if relevant_exists else ""
    with conn.cursor() as cur:
        noise_query = f"""
            SELECT id, canonical_name, county FROM subdivisions
            WHERE is_active = TRUE
              {relevant_clause}
              AND NOT EXISTS (SELECT 1 FROM parcels WHERE parcels.subdivision_id = subdivisions.id)
              AND NOT EXISTS (SELECT 1 FROM cr_entitlement_actions WHERE cr_entitlement_actions.subdivision_id = subdivisions.id)
              AND NOT EXISTS (SELECT 1 FROM transactions WHERE transactions.subdivision_id = subdivisions.id)
              AND NOT EXISTS (SELECT 1 FROM pt_permits WHERE pt_permits.subdivision_id = subdivisions.id)
              AND NOT EXISTS (SELECT 1 FROM subdivision_aliases WHERE subdivision_aliases.subdivision_id = subdivisions.id)
            ORDER BY county, canonical_name
        """
        cur.execute(noise_query)
        rows = cur.fetchall()

    count = len(rows)
    if count == 0:
        print("  No noise subdivisions to deactivate")
        return 0

    print(f"  {count} noise subdivisions identified (no parcels, no actions, no transactions, no permits, no aliases)")
    if count <= 20:
        for r in rows:
            print(f"    - [{r[0]}] {r[2]}: {r[1]}")
    else:
        # Show county-level breakdown
        by_county: dict[str, int] = {}
        for r in rows:
            by_county[r[2]] = by_county.get(r[2], 0) + 1
        for county, cnt in sorted(by_county.items()):
            print(f"    {county}: {cnt}")

    if DRY_RUN:
        print(f"  [DRY RUN] would deactivate {count} noise subdivisions")
        return count

    with conn.cursor() as cur:
        cur.execute(f"""
            UPDATE subdivisions SET is_active = FALSE
            WHERE is_active = TRUE
              {relevant_clause}
              AND NOT EXISTS (SELECT 1 FROM parcels WHERE parcels.subdivision_id = subdivisions.id)
              AND NOT EXISTS (SELECT 1 FROM cr_entitlement_actions WHERE cr_entitlement_actions.subdivision_id = subdivisions.id)
              AND NOT EXISTS (SELECT 1 FROM transactions WHERE transactions.subdivision_id = subdivisions.id)
              AND NOT EXISTS (SELECT 1 FROM pt_permits WHERE pt_permits.subdivision_id = subdivisions.id)
              AND NOT EXISTS (SELECT 1 FROM subdivision_aliases WHERE subdivision_aliases.subdivision_id = subdivisions.id)
        """)
        updated = cur.rowcount
    conn.commit()
    print(f"  {updated} noise subdivisions deactivated")
    return updated


# ---------------------------------------------------------------------------
# Commission Radar cleanup
# ---------------------------------------------------------------------------

def add_cr_config_is_active(conn):
    """Add is_active column to cr_jurisdiction_config if it doesn't exist."""
    with conn.cursor() as cur:
        if _col_exists(cur, "cr_jurisdiction_config", "is_active"):
            print("  cr_jurisdiction_config.is_active already exists, skipping")
            return 0
        if DRY_RUN:
            print("  [DRY RUN] would add cr_jurisdiction_config.is_active column")
            return 0
        cur.execute("""
            ALTER TABLE cr_jurisdiction_config
            ADD COLUMN is_active BOOLEAN DEFAULT TRUE
        """)
    conn.commit()
    print("  cr_jurisdiction_config.is_active column added")
    return 1


def deactivate_boa_configs(conn):
    """Set is_active=FALSE for board_of_adjustment jurisdiction configs."""
    with conn.cursor() as cur:
        if DRY_RUN:
            cur.execute("""
                SELECT count(*) FROM cr_jurisdiction_config
                WHERE commission_type = 'board_of_adjustment'
            """)
            count = cur.fetchone()[0]
            print(f"  [DRY RUN] would deactivate {count} BOA jurisdiction configs")
            return count

        cur.execute("""
            UPDATE cr_jurisdiction_config
            SET is_active = FALSE
            WHERE commission_type = 'board_of_adjustment'
        """)
        count = cur.rowcount
    conn.commit()
    print(f"  {count} BOA jurisdiction configs deactivated")
    return count


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(conn):
    """Print current state of builders and subdivisions for verification."""
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM builders WHERE is_active = TRUE")
        active_builders = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM builders WHERE is_active = FALSE")
        inactive_builders = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM subdivisions WHERE is_active = TRUE")
        active_subs = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM subdivisions WHERE is_active = FALSE")
        inactive_subs = cur.fetchone()[0]

        relevant_subs = "?"
        if _col_exists(cur, "subdivisions", "is_relevant"):
            cur.execute("SELECT count(*) FROM subdivisions WHERE is_relevant = TRUE")
            relevant_subs = cur.fetchone()[0]

        active_configs = "?"
        inactive_configs = "?"
        if _col_exists(cur, "cr_jurisdiction_config", "is_active"):
            cur.execute("SELECT count(*) FROM cr_jurisdiction_config WHERE is_active = TRUE")
            active_configs = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM cr_jurisdiction_config WHERE is_active = FALSE")
            inactive_configs = cur.fetchone()[0]

    print(f"\n  Builders:     {active_builders} active, {inactive_builders} inactive")
    print(f"  Subdivisions: {active_subs} active ({relevant_subs} relevant), {inactive_subs} inactive")
    print(f"  CR configs:   {active_configs} active, {inactive_configs} inactive")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    mode = "DRY RUN" if DRY_RUN else "LIVE"
    print(f"004_backend_cleanup [{mode}] — Schema additions and data cleanup")
    print("=" * 60)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        print("\n1. Builder source column")
        add_builder_source_column(conn)

        print("\n2. Mark auto-inserted builders")
        mark_auto_inserted_builders(conn)

        print("\n3. Mark seed builders")
        mark_seed_builders(conn)

        print("\n4. Subdivision is_relevant column")
        add_subdivision_is_relevant(conn)

        print("\n5. Backfill subdivision relevance")
        backfill_subdivision_relevance(conn)

        print("\n6. Deactivate noise subdivisions")
        deactivate_noise_subdivisions(conn)

        print("\n7. CR jurisdiction config is_active column")
        add_cr_config_is_active(conn)

        print("\n8. Deactivate BOA jurisdiction configs")
        deactivate_boa_configs(conn)

        print("\n--- Summary ---")
        print_summary(conn)

        print("\n" + "=" * 60)
        print("Done.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
