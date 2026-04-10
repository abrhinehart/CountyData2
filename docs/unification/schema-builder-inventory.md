# Builder Inventory — Schema Summary

**Database**: PostgreSQL + PostGIS, `postgresql://inventory_user:changeme@localhost:1100/builder_inventory`  
**ORM**: SQLAlchemy 2.0 (mapped_column) + Alembic  
**Migrations**: 8 Alembic revisions

## Tables

### builders
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| canonical_name | String | UNIQUE, NOT NULL |
| type | String | NOT NULL, default 'builder' — builder/developer/land_banker/btr |
| is_active | Boolean | default true |
| scope | String | NOT NULL, default 'national' — national or regional |
| created_at | DateTime(tz) | default now() |
| updated_at | DateTime(tz) | default now(), auto-update |

Seeded from CountyData2's `builders.yaml` and `land_bankers.yaml`

### builder_aliases
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| builder_id | Integer | FK -> builders.id CASCADE, NOT NULL |
| alias | String | NOT NULL, indexed |

**Unique**: (builder_id, alias)

### builder_counties (junction for regional scope)
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| builder_id | Integer | FK -> builders.id CASCADE, NOT NULL |
| county_id | Integer | FK -> counties.id CASCADE, NOT NULL |

**Unique**: (builder_id, county_id)

### counties
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| name | String | NOT NULL |
| state | String(2) | NOT NULL, default 'FL' |
| dor_county_no | Integer | nullable |
| county_fips | String | nullable |
| gis_endpoint | String | nullable — ArcGIS FeatureServer URL |
| gis_owner_field | String | nullable |
| gis_parcel_field | String | nullable |
| gis_address_field | String | nullable |
| gis_use_field | String | nullable |
| gis_acreage_field | String | nullable |
| gis_subdivision_field | String | nullable |
| gis_building_value_field | String | nullable |
| gis_appraised_value_field | String | nullable |
| gis_deed_date_field | String | nullable |
| gis_previous_owner_field | String | nullable |
| gis_max_records | Integer | default 1000 |
| is_active | Boolean | default true |
| created_at | DateTime(tz) | default now() |
| updated_at | DateTime(tz) | default now(), auto-update |

**Unique**: (name, state)

### subdivisions
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| name | String | NOT NULL |
| county_id | Integer | FK -> counties.id, NOT NULL |
| geom | Geometry(MULTIPOLYGON, 4326) | nullable |
| created_at | DateTime(tz) | default now() |
| updated_at | DateTime(tz) | default now(), auto-update |

**Unique**: (name, county_id)  
Auto-created from GIS or imported via GeoJSON API.

### parcels (core inventory table)
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| parcel_number | String | NOT NULL |
| county_id | Integer | FK -> counties.id, NOT NULL |
| builder_id | Integer | FK -> builders.id, nullable |
| subdivision_id | Integer | FK -> subdivisions.id, nullable |
| owner_name | String | nullable |
| site_address | String | nullable |
| use_type | String | nullable |
| acreage | Numeric(10,4) | nullable |
| centroid | Geometry(POINT, 4326) | nullable |
| geom | Geometry(MULTIPOLYGON, 4326) | nullable |
| parcel_class | String | nullable — lot/common_area/tract/other |
| lot_width_ft | Numeric(10,1) | nullable |
| lot_depth_ft | Numeric(10,1) | nullable |
| lot_area_sqft | Numeric(12,1) | nullable |
| building_value | Numeric(14,2) | nullable |
| appraised_value | Numeric(14,2) | nullable |
| deed_date | DateTime(tz) | nullable |
| previous_owner | String | nullable |
| is_active | Boolean | default true |
| first_seen | DateTime(tz) | default now() |
| last_seen | DateTime(tz) | default now() |
| last_changed | DateTime(tz) | default now() |

**Unique**: (parcel_number, county_id)

### snapshots (scrape audit log)
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| county_id | Integer | FK -> counties.id, NOT NULL |
| started_at | DateTime(tz) | default now() |
| completed_at | DateTime(tz) | nullable |
| status | String | default 'running' — running/completed/failed |
| total_parcels_queried | Integer | default 0 |
| new_count | Integer | default 0 |
| removed_count | Integer | default 0 |
| changed_count | Integer | default 0 |
| unchanged_count | Integer | default 0 |
| error_message | String | nullable |
| summary_text | String | nullable |

### parcel_snapshots (per-parcel change records)
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| parcel_id | Integer | FK -> parcels.id, NOT NULL |
| snapshot_id | Integer | FK -> snapshots.id, NOT NULL |
| change_type | String | NOT NULL — new/removed/changed |
| old_values | JSONB | nullable |
| new_values | JSONB | nullable |
| created_at | DateTime(tz) | default now() |

### schedule_config (singleton)
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK, always 1 |
| interval_minutes | Integer | default 10080 (7 days) |
| is_enabled | Boolean | default true |
| updated_at | DateTime(tz) | default now(), auto-update |
