"""
seed_pt_jurisdiction_config.py - Seed PT jurisdiction configs and watchlist subdivisions.

Creates jurisdictions in the shared table, then populates pt_jurisdiction_config
with portal/adapter details. Also sets the watched flag on matching subdivisions.

Idempotent: uses ON CONFLICT.

Usage:
    python seed_pt_jurisdiction_config.py
"""

import psycopg2

from config import DATABASE_URL

# PT jurisdictions: (name, county_name, municipality, state, adapter_slug, adapter_class, portal_type, portal_url, scrape_mode, fragile_note)
JURISDICTIONS = [
    ("Bay County", "Bay", None, "FL", "bay-county",
     "modules.permits.scrapers.adapters.bay_county.BayCountyAdapter",
     "cityview", "https://portal.baycountyfl.gov/", "live", None),
    ("Panama City", "Bay", "Panama City", "FL", "panama-city",
     "modules.permits.scrapers.adapters.panama_city.PanamaCityAdapter",
     "cloudpermit", "https://www.panamacity.gov/803/Cloudpermit", "live", None),
    ("Panama City Beach", "Bay", "Panama City Beach", "FL", "panama-city-beach",
     "modules.permits.scrapers.adapters.panama_city_beach.PanamaCityBeachAdapter",
     "iworq", "https://www.pcbfl.gov/219/Permit-Inspection-Search", "live", None),
    ("Polk County", "Polk", None, "FL", "polk-county",
     "modules.permits.scrapers.adapters.polk_county.PolkCountyAdapter",
     "accela", "https://aca-prod.accela.com/POLKCO/Default.aspx", "live", None),
    ("Okeechobee County", "Okeechobee", None, "FL", "okeechobee",
     "modules.permits.scrapers.adapters.okeechobee.OkeechobeeAdapter",
     "tyler-energov", "https://okeechobeecountyfl-energovweb.tylerhost.net/apps/selfservice",
     "live", None),
    ("Hernando County", "Hernando", None, "FL", "hernando-county",
     "modules.permits.scrapers.adapters.hernando_county.HernandoCountyAdapter",
     "tyler-energov", "https://hernandocountyfl-energovweb.tylerhost.net/apps/selfservice",
     "live", None),
    ("Marion County", "Marion", None, "FL", "marion-county",
     "modules.permits.scrapers.adapters.marion_county.MarionCountyAdapter",
     "tyler-energov", "https://selfservice.marionfl.org/energov_prod/selfservice",
     "live", None),
    ("Walton County", "Walton", None, "FL", "walton-county",
     "modules.permits.scrapers.adapters.walton_county.WaltonCountyAdapter",
     "tyler-energov", "https://waltoncountyfl-energovweb.tylerhost.net/apps/SelfService",
     "live", None),
    ("DeSoto County, MS", "DeSoto", None, "MS", "desoto-county-ms",
     "modules.permits.scrapers.adapters.desoto_county_ms.DeSotoCountyMsAdapter",
     "tyler-energov", "https://energovweb.desotocountyms.gov/energov_prod/selfservice",
     "live", None),
    ("Citrus County", "Citrus", None, "FL", "citrus-county",
     "modules.permits.scrapers.adapters.citrus_county.CitrusCountyAdapter",
     "accela", "https://aca-prod.accela.com/CITRUS/Default.aspx",
     "live", None),
    ("Madison County, AL", "Madison", None, "AL", "madison-county-al",
     "modules.permits.scrapers.adapters.madison_county_al.MadisonCountyAlAdapter",
     "cityview", "https://cityview.madisoncountyal.gov/Portal", "live",
     "Authenticated CityView scraper is live, but brittle enough that reruns and manual verification are still prudent."),
    ("Winter Haven", "Polk", "Winter Haven", "FL", "winter-haven",
     "modules.permits.scrapers.adapters.winter_haven.WinterHavenAdapter",
     "accela", "https://aca-prod.accela.com/COWH/Default.aspx", "live", None),
    ("Lake Alfred", "Polk", "Lake Alfred", "FL", "lake-alfred",
     "modules.permits.scrapers.adapters.lake_alfred.LakeAlfredAdapter",
     "accela", "https://aca-prod.accela.com/COLA/Default.aspx", "live", None),
    ("Haines City", "Polk", "Haines City", "FL", "haines-city",
     "modules.permits.scrapers.adapters.haines_city.HainesCityAdapter",
     "iworq", "https://haines.portal.iworq.net/HAINES/permits/600", "live", None),
    ("Davenport", "Polk", "Davenport", "FL", "davenport",
     "modules.permits.scrapers.adapters.davenport.DavenportAdapter",
     "iworq", "https://portal.iworq.net/DAVENPORT/permits/600", "live", None),
    ("Lake Hamilton", "Polk", "Lake Hamilton", "FL", "lake-hamilton",
     "modules.permits.scrapers.adapters.lake_hamilton.LakeHamiltonAdapter",
     "iworq", "https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permits/600",
     "live", "iWorQ portal uses reCAPTCHA and has no date-range search. Needs browser-based scraper."),
]

# Subdivisions to mark as watched (name, jurisdiction_name, notes)
WATCHLIST = [
    ("Breakfast Point East", "Panama City Beach", "Seeded from PRD watchlist."),
    ("SweetBay", "Panama City", "Master-planned bayfront community."),
    ("Ward Creek", "Panama City Beach", "Tracked for coastal activity."),
    ("Salt Creek", "Bay County", "Seeded from reference list."),
    ("Titus Park", "Panama City", "Monitored for builder mix."),
    ("Liberty", "Bay County", "Includes multiple active phases."),
]


def main():
    conn = psycopg2.connect(DATABASE_URL)
    jurisdictions_created = 0
    configs_upserted = 0
    watched_set = 0

    try:
        with conn.cursor() as cur:
            for (jname, county_name, municipality, state,
                 adapter_slug, adapter_class, portal_type, portal_url,
                 scrape_mode, fragile_note) in JURISDICTIONS:

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
                    print(f"  created county: {county_name}, {state}")
                else:
                    county_id = row[0]

                # Determine jurisdiction type
                jtype = "city" if municipality else "county"
                slug = adapter_slug

                # Upsert jurisdiction
                cur.execute("""
                    INSERT INTO jurisdictions (slug, name, county_id, municipality, jurisdiction_type)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name, county_id) DO UPDATE SET
                        slug = EXCLUDED.slug,
                        municipality = EXCLUDED.municipality,
                        jurisdiction_type = EXCLUDED.jurisdiction_type
                    RETURNING id
                """, (slug, jname, county_id, municipality, jtype))
                jurisdiction_id = cur.fetchone()[0]
                jurisdictions_created += 1

                # Upsert pt_jurisdiction_config
                cur.execute("""
                    INSERT INTO pt_jurisdiction_config
                        (jurisdiction_id, adapter_slug, adapter_class, portal_type, portal_url,
                         scrape_mode, fragile_note)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (jurisdiction_id) DO UPDATE SET
                        adapter_slug = EXCLUDED.adapter_slug,
                        adapter_class = EXCLUDED.adapter_class,
                        portal_type = EXCLUDED.portal_type,
                        portal_url = EXCLUDED.portal_url,
                        scrape_mode = EXCLUDED.scrape_mode,
                        fragile_note = EXCLUDED.fragile_note
                """, (jurisdiction_id, adapter_slug, adapter_class, portal_type, portal_url,
                      scrape_mode, fragile_note))
                configs_upserted += 1

            # Set watched flag on matching subdivisions
            for sub_name, jname, notes in WATCHLIST:
                # Find the county for this jurisdiction
                cur.execute("""
                    SELECT j.county_id FROM jurisdictions j WHERE j.name = %s LIMIT 1
                """, (jname,))
                row = cur.fetchone()
                if not row:
                    continue
                county_id = row[0]

                # Find the subdivision by canonical_name and county
                cur.execute("""
                    SELECT s.id FROM subdivisions s
                    JOIN counties c ON c.id = s.county_id
                    WHERE UPPER(s.canonical_name) = UPPER(%s)
                      AND s.county_id = %s
                    LIMIT 1
                """, (sub_name, county_id))
                row = cur.fetchone()
                if not row:
                    # Try alias match
                    cur.execute("""
                        SELECT s.id FROM subdivisions s
                        JOIN subdivision_aliases sa ON sa.subdivision_id = s.id
                        WHERE UPPER(sa.alias) = UPPER(%s)
                          AND s.county_id = %s
                        LIMIT 1
                    """, (sub_name, county_id))
                    row = cur.fetchone()

                if row:
                    cur.execute("""
                        UPDATE subdivisions SET watched = TRUE, notes = %s
                        WHERE id = %s AND NOT watched
                    """, (notes, row[0]))
                    if cur.rowcount:
                        watched_set += 1
                        print(f"  watched: {sub_name}")
                else:
                    print(f"  skip watch (not found): {sub_name} in {jname}")

        conn.commit()
    finally:
        conn.close()

    print(f"\npt_jurisdiction_config: {configs_upserted} configs, {jurisdictions_created} jurisdictions.")
    print(f"Watchlist: {watched_set} subdivisions marked as watched.")
    print("Done.")


if __name__ == "__main__":
    main()
