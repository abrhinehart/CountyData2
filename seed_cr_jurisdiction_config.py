"""
seed_cr_jurisdiction_config.py - Seed Commission Radar jurisdiction configs from YAML files.

Reads YAML jurisdiction definitions from modules/commission/config/jurisdictions/{STATE}/
and upserts:
  1. A row in shared `jurisdictions` (name, county, state, municipality)
  2. A row in `cr_jurisdiction_config` (commission_type, agenda_platform, config_json, etc.)

Idempotent: uses ON CONFLICT.

Reconciles DB state with disk state: any cr_jurisdiction_config row whose
jurisdiction is no longer represented by a YAML on disk is set to
is_active=False (pass --no-deactivate-missing to suppress). Without this,
YAML deletions silently leave stale-active rows behind on the dashboard.

Usage:
    python seed_cr_jurisdiction_config.py [--no-deactivate-missing]
"""

import argparse
import json
from pathlib import Path

import psycopg2
import yaml

from config import DATABASE_URL

CONFIG_DIR = Path(__file__).parent / "modules" / "commission" / "config" / "jurisdictions"


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def seed(deactivate_missing: bool = True):
    conn = psycopg2.connect(DATABASE_URL)
    jurisdictions_upserted = 0
    configs_upserted = 0
    skipped = 0
    counties_created = 0
    seeded_jurisdiction_ids: set[int] = set()
    deactivated = 0

    try:
        with conn.cursor() as cur:
            for state_dir in sorted(CONFIG_DIR.glob("*")):
                if not state_dir.is_dir():
                    continue
                state = state_dir.name
                for yaml_file in sorted(state_dir.glob("*.yaml")):
                    # Skip defaults files (prefixed with underscore)
                    if yaml_file.name.startswith("_"):
                        continue

                    try:
                        data = load_yaml(yaml_file)
                    except Exception as exc:
                        print(f"  skip (parse error): {yaml_file.name} - {exc}")
                        skipped += 1
                        continue

                    name = data.get("name")
                    slug = data.get("slug") or yaml_file.stem
                    county_name = data.get("county")
                    municipality = data.get("municipality") or None
                    commission_type = data.get("commission_type")
                    if not (name and county_name and commission_type):
                        print(f"  skip (missing fields): {yaml_file.name}")
                        skipped += 1
                        continue

                    # Ensure county exists
                    cur.execute(
                        "SELECT id FROM counties WHERE name = %s AND state = %s",
                        (county_name, state),
                    )
                    row = cur.fetchone()
                    if not row:
                        cur.execute(
                            "INSERT INTO counties (name, state) VALUES (%s, %s) RETURNING id",
                            (county_name, state),
                        )
                        county_id = cur.fetchone()[0]
                        counties_created += 1
                        print(f"  created county: {county_name}, {state}")
                    else:
                        county_id = row[0]

                    # Upsert jurisdiction in shared table
                    jtype = "city" if municipality else "county"
                    cur.execute(
                        """
                        INSERT INTO jurisdictions
                            (slug, name, county_id, municipality, jurisdiction_type)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (name, county_id) DO UPDATE SET
                            slug = EXCLUDED.slug,
                            municipality = EXCLUDED.municipality,
                            jurisdiction_type = EXCLUDED.jurisdiction_type
                        RETURNING id
                        """,
                        (slug, name, county_id, municipality, jtype),
                    )
                    jurisdiction_id = cur.fetchone()[0]
                    jurisdictions_upserted += 1
                    seeded_jurisdiction_ids.add(jurisdiction_id)

                    # Build config_json from non-trivial fields
                    config_blob = {
                        "keywords": data.get("keywords", []),
                        "detection_patterns": data.get("detection_patterns", {}),
                        "extraction_notes": data.get("extraction_notes"),
                        "scraping": data.get("scraping", {}),
                    }

                    # Upsert cr_jurisdiction_config
                    scraping = data.get("scraping", {}) or {}
                    agenda_platform = scraping.get("platform")
                    agenda_source_url = scraping.get("base_url")
                    has_duplicate_page_bug = bool(scraping.get("has_duplicate_page_bug", False))

                    cur.execute(
                        """
                        INSERT INTO cr_jurisdiction_config
                            (jurisdiction_id, commission_type, agenda_source_url,
                             agenda_platform, has_duplicate_page_bug, pinned, config_json)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (jurisdiction_id) DO UPDATE SET
                            commission_type = EXCLUDED.commission_type,
                            agenda_source_url = EXCLUDED.agenda_source_url,
                            agenda_platform = EXCLUDED.agenda_platform,
                            has_duplicate_page_bug = EXCLUDED.has_duplicate_page_bug,
                            config_json = EXCLUDED.config_json
                        """,
                        (
                            jurisdiction_id,
                            commission_type,
                            agenda_source_url,
                            agenda_platform,
                            has_duplicate_page_bug,
                            False,  # pinned default
                            json.dumps(config_blob),
                        ),
                    )
                    configs_upserted += 1

            if deactivate_missing and seeded_jurisdiction_ids:
                cur.execute(
                    """
                    UPDATE cr_jurisdiction_config
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE is_active = TRUE
                      AND jurisdiction_id <> ALL(%s)
                    """,
                    (list(seeded_jurisdiction_ids),),
                )
                deactivated = cur.rowcount

        conn.commit()
    finally:
        conn.close()

    print()
    print(f"Jurisdictions upserted: {jurisdictions_upserted}")
    print(f"CR configs upserted:    {configs_upserted}")
    print(f"Counties created:       {counties_created}")
    print(f"Skipped:                {skipped}")
    if deactivate_missing:
        print(f"Stale configs deactivated: {deactivated}")
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-deactivate-missing",
        dest="deactivate_missing",
        action="store_false",
        help="Skip the end-of-run pass that sets is_active=FALSE on "
             "cr_jurisdiction_config rows whose YAML was deleted.",
    )
    args = parser.parse_args()
    seed(deactivate_missing=args.deactivate_missing)
