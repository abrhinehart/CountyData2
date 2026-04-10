# Permit Tracker — Schema Summary

**Database**: SQLite, `data/permit_tracker.db`  
**ORM**: None (raw sqlite3 with Row factory)  
**Migrations**: Imperative, run on every init_db()  
**External dependency**: Reads CountyData2 PostGIS for subdivision geometry lookups

## Tables

### jurisdictions
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| name | TEXT | NOT NULL, UNIQUE |
| portal_type | TEXT | NOT NULL |
| portal_url | TEXT | NOT NULL |
| active | INTEGER | NOT NULL, DEFAULT 1 |

Seeded from `data/jurisdiction_registry.json`

### subdivisions
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| name | TEXT | NOT NULL |
| jurisdiction_id | INTEGER | NOT NULL FK -> jurisdictions(id) |
| watched | INTEGER | NOT NULL, DEFAULT 0 |
| notes | TEXT | nullable |

**Unique**: (name, jurisdiction_id)  
Seeded from `jurisdiction_registry.json` subdivisions array.

### builders
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| name | TEXT | NOT NULL, UNIQUE |

Auto-created from permit contractor names via `canonicalize_builder_name()`. No alias table — uses function-based canonicalization (DBA extraction, email-domain matching, suffix removal, ~30 known builders lookup).

### permits (central fact table)
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| permit_number | TEXT | NOT NULL |
| jurisdiction_id | INTEGER | NOT NULL FK -> jurisdictions(id) |
| subdivision_id | INTEGER | nullable FK -> subdivisions(id) |
| builder_id | INTEGER | nullable FK -> builders(id) |
| address | TEXT | NOT NULL |
| parcel_id | TEXT | nullable |
| issue_date | TEXT | NOT NULL (ISO date) |
| status | TEXT | NOT NULL |
| permit_type | TEXT | NOT NULL |
| valuation | REAL | nullable |
| raw_subdivision_name | TEXT | nullable |
| raw_contractor_name | TEXT | nullable |
| raw_applicant_name | TEXT | nullable |
| raw_licensed_professional_name | TEXT | nullable |
| latitude | REAL | nullable |
| longitude | REAL | nullable |
| first_seen_at | TEXT | NOT NULL (ISO timestamp) |
| last_updated_at | TEXT | NOT NULL (ISO timestamp) |
| last_seen_at | TEXT | NOT NULL (ISO timestamp) |

**Unique**: (jurisdiction_id, permit_number)

### scrape_runs
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| jurisdiction_id | INTEGER | NOT NULL FK -> jurisdictions(id) |
| run_at | TEXT | NOT NULL |
| status | TEXT | NOT NULL |
| permits_found | INTEGER | NOT NULL, DEFAULT 0 |
| permits_new | INTEGER | NOT NULL, DEFAULT 0 |
| permits_updated | INTEGER | NOT NULL, DEFAULT 0 |
| error_log | TEXT | nullable |

### scrape_payload_archives
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| jurisdiction_id | INTEGER | NOT NULL FK -> jurisdictions(id) |
| run_at | TEXT | NOT NULL |
| status | TEXT | NOT NULL |
| permits_count | INTEGER | NOT NULL, DEFAULT 0 |
| source_start_date | TEXT | nullable |
| source_end_date | TEXT | nullable |
| payload_json | TEXT | NOT NULL (JSON array) |

### scrape_jobs (durable job queue)
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| jurisdiction_name | TEXT | nullable (NULL = all) |
| status | TEXT | NOT NULL — pending/running/succeeded/failed |
| trigger_type | TEXT | NOT NULL — manual/scheduler/retry |
| request_payload_json | TEXT | NOT NULL |
| attempt_count | INTEGER | NOT NULL, DEFAULT 0 |
| max_attempts | INTEGER | NOT NULL, DEFAULT 1 |
| retry_of_job_id | INTEGER | nullable FK -> scrape_jobs(id) |
| queued_at | TEXT | NOT NULL |
| started_at | TEXT | nullable |
| lease_expires_at | TEXT | nullable |
| finished_at | TEXT | nullable |
| last_error | TEXT | nullable |
| result_summary_json | TEXT | nullable |
| scrape_run_id | INTEGER | nullable FK -> scrape_runs(id) |

### scraper_artifacts (HTTP traces)
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| jurisdiction_id | INTEGER | nullable FK -> jurisdictions(id) |
| adapter_slug | TEXT | NOT NULL |
| scrape_job_id | INTEGER | nullable FK -> scrape_jobs(id) |
| scrape_run_id | INTEGER | nullable FK -> scrape_runs(id) |
| artifact_type | TEXT | NOT NULL |
| method | TEXT | nullable |
| url | TEXT | nullable |
| status_code | INTEGER | nullable |
| content_type | TEXT | nullable |
| excerpt_text | TEXT | nullable |
| metadata_json | TEXT | NOT NULL |
| created_at | TEXT | NOT NULL |

### geocode_cache
| Column | Type | Constraints |
|---|---|---|
| address | TEXT | PK |
| latitude | REAL | nullable |
| longitude | REAL | nullable |
| matched_address | TEXT | nullable |
| match_type | TEXT | nullable |
| match_status | TEXT | NOT NULL |
| geocoded_at | TEXT | NOT NULL |

### parcel_lookup_cache
| Column | Type | Constraints |
|---|---|---|
| address | TEXT | PK |
| parcel_id | TEXT | nullable |
| matched_address | TEXT | nullable |
| site_address | TEXT | nullable |
| owner_name | TEXT | nullable |
| match_type | TEXT | nullable |
| match_status | TEXT | NOT NULL |
| looked_up_at | TEXT | NOT NULL |

### adapter_record_cache
| Column | Type | Constraints |
|---|---|---|
| adapter_slug | TEXT | NOT NULL |
| record_key | TEXT | NOT NULL |
| payload_json | TEXT | NOT NULL |
| updated_at | TEXT | NOT NULL |

**PK**: (adapter_slug, record_key)

### adapter_state
| Column | Type | Constraints |
|---|---|---|
| adapter_slug | TEXT | NOT NULL |
| state_key | TEXT | NOT NULL |
| state_value | TEXT | NOT NULL |
| updated_at | TEXT | NOT NULL |

**PK**: (adapter_slug, state_key)

## Adapter Registry
- bay-county (CityView PDF), panama-city (Cloudpermit GeoJSON), panama-city-beach (iWorq HTML), polk-county (Accela ASP.NET), madison-county-al (CityView authenticated), okeechobee (fixture), citrus-county (fixture)
