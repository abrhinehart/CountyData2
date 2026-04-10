# CountyData2 — Schema Summary

**Database**: PostgreSQL 16 + PostGIS 3.4, `postgresql://etl_user:changeme@localhost:5432/County-Data`  
**Docker**: `postgis/postgis:16-3.4`, schema bootstrapped via `schema.sql` mounted into init dir  
**Migrations**: 12 additive SQL files in `migrations/`

## Tables

### transactions (central fact table)
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| grantor | TEXT | NOT NULL |
| grantee | TEXT | nullable |
| type | TEXT | nullable — classified transaction type |
| instrument | TEXT | nullable — document type from clerk portal |
| date | DATE | nullable |
| export_legal_desc | TEXT | nullable — cleaned legal description |
| export_legal_raw | TEXT | nullable — original legal before cleaning |
| deed_locator | JSONB | DEFAULT '{}' — book/page/instrument locator |
| deed_legal_desc | TEXT | nullable — legal from deed document |
| deed_legal_parsed | JSONB | DEFAULT '{}' — structured parse of deed legal |
| subdivision | TEXT | nullable — canonical subdivision name |
| subdivision_id | INTEGER | FK -> subdivisions(id) |
| phase | TEXT | nullable |
| inventory_category | TEXT | nullable |
| lots | INTEGER | DEFAULT 1 |
| price | NUMERIC(15,2) | nullable |
| price_per_lot | NUMERIC(15,2) | nullable |
| acres | NUMERIC(10,4) | nullable |
| acres_source | TEXT | nullable |
| price_per_acre | NUMERIC(15,2) | nullable |
| parsed_data | JSONB | DEFAULT '{}' — county parser output |
| county | TEXT | NOT NULL — string like "Bay", "Jackson MS" |
| notes | TEXT | nullable |
| builder_id | INTEGER | FK -> builders(id) — legacy, prefers buyer-side |
| grantor_builder_id | INTEGER | FK -> builders(id) |
| grantee_builder_id | INTEGER | FK -> builders(id) |
| grantor_land_banker_id | INTEGER | FK -> land_bankers(id) |
| grantee_land_banker_id | INTEGER | FK -> land_bankers(id) |
| review_flag | BOOLEAN | DEFAULT FALSE |
| mortgage_amount | NUMERIC(15,2) | nullable |
| mortgage_originator | TEXT | nullable |
| grantor_key | TEXT | GENERATED ALWAYS AS UPPER(TRIM(grantor)) STORED |
| grantee_key | TEXT | GENERATED ALWAYS AS UPPER(TRIM(COALESCE(grantee,''))) STORED |
| instrument_key | TEXT | GENERATED ALWAYS AS UPPER(TRIM(COALESCE(instrument,''))) STORED |
| county_key | TEXT | GENERATED ALWAYS AS UPPER(TRIM(county)) STORED |
| source_file | TEXT | nullable |
| inserted_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

**Unique**: (grantor_key, grantee_key, instrument_key, date, county_key)  
**Indexes**: county, subdivision, subdivision_id, inventory_category (partial), builder_id, grantor_builder_id, grantee_builder_id, grantor_land_banker_id, grantee_land_banker_id, date, review_flag (partial)

### transaction_segments
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| transaction_id | INTEGER | NOT NULL FK -> transactions(id) CASCADE |
| segment_index | INTEGER | NOT NULL |
| county | TEXT | NOT NULL |
| subdivision_lookup_text | TEXT | nullable |
| raw_subdivision | TEXT | nullable |
| subdivision | TEXT | nullable |
| subdivision_id | INTEGER | FK -> subdivisions(id) |
| phase_raw | TEXT | nullable |
| phase | TEXT | nullable |
| inventory_category | TEXT | nullable |
| phase_confirmed | BOOLEAN | nullable |
| segment_review_reasons | TEXT[] | DEFAULT '{}' |
| segment_data | JSONB | DEFAULT '{}' |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

**Unique**: (transaction_id, segment_index)

### subdivisions
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| canonical_name | TEXT | NOT NULL |
| county | TEXT | NOT NULL |
| phases | TEXT[] | DEFAULT '{}' |
| county_id | INTEGER | FK -> counties(id) |
| geom | GEOMETRY(MultiPolygon, 4326) | nullable |
| source | TEXT | nullable |
| plat_book | TEXT | nullable |
| plat_page | TEXT | nullable |
| developer_name | TEXT | nullable |
| recorded_date | DATE | nullable |
| platted_acreage | DOUBLE PRECISION | nullable |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

**Unique**: (canonical_name, county)  
**Indexes**: geom (GIST), county_id, source

### subdivision_aliases
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| subdivision_id | INTEGER | NOT NULL FK -> subdivisions(id) CASCADE |
| alias | TEXT | NOT NULL |

**Unique**: (alias, subdivision_id)  
**Index**: UPPER(alias)

### builders
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| canonical_name | TEXT | NOT NULL UNIQUE |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

25 builders seeded from `reference_data/builders.yaml`

### builder_aliases
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| builder_id | INTEGER | NOT NULL FK -> builders(id) CASCADE |
| alias | TEXT | NOT NULL UNIQUE |

**Index**: UPPER(alias)

### land_bankers
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| canonical_name | TEXT | NOT NULL UNIQUE |
| category | TEXT | nullable — 'land_banker', 'developer', or 'btr' |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

32 entities across 3 categories, seeded from `reference_data/land_bankers.yaml`

### land_banker_aliases
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| land_banker_id | INTEGER | NOT NULL FK -> land_bankers(id) CASCADE |
| alias | TEXT | NOT NULL UNIQUE |

### counties
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| name | TEXT | NOT NULL UNIQUE |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

67 Florida counties seeded. No state column.

## Transaction Type Enum (application-level)
- House Sale, Builder Purchase, Builder to Builder, Land Banker Purchase, Build-to-Rent Purchase, Raw Land Purchase, CDD Transfer, Association Transfer, Correction / Quit Claim

## Active Counties
Bay FL, Citrus FL, Escambia FL, Hernando FL, Okeechobee FL, Walton FL, DeSoto MS, Harrison MS, Hinds MS, Jackson MS, Madison MS, Rankin MS, Madison AL
