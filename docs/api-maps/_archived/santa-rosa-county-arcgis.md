# Santa Rosa County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Online FeatureServer (Esri-hosted; not county-hosted) |
| Endpoint | `https://services.arcgis.com/Eg4L1xEv2R3abuQd/arcgis/rest/services/ParcelsOpenData/FeatureServer/0` |
| Layer Name | ParcelsOpenData (ID 0) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 103024 / latestWkid 6441 (NAD_1983_2011_StatePlane_Florida_North_FIPS_0903_Ft_US) |
| Max Record Count | 2000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Display Field | StrName |
| ObjectId Field | FID |
| Global ID Field | GlobalID (String, not the native GlobalID type) |
| Capabilities | `Query,Extract` |
| Registry status | `bi` active (per `county-registry.yaml` L348-352) |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Santa Rosa field mapping (from `seed_bi_county_config.py` L261-268)

| Purpose | Santa Rosa Field |
|---------|------------------|
| Owner | `OwnerName` |
| Parcel | `ParcelDisp` |
| Address | `Addr1` |
| Use | `PRuse` |
| Acreage | `CALC_ACRE` |

**Note on `PRuse` lowercase:** The use field name mixes case (`PRuse`, not `PRUSE` or `PRUse`). Changing case would break queries -- ArcGIS field names are case-sensitive in many deployments. A sibling `PropertyUs` field also exists (see Field Inventory); the seed configuration uses `PRuse` (the short code), not `PropertyUs` (the longer description).

---

## 2. Query Capabilities

Base query URL:

```
https://services.arcgis.com/Eg4L1xEv2R3abuQd/arcgis/rest/services/ParcelsOpenData/FeatureServer/0/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `OwnerName LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from StatePlane FL North (ft) to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 2000 | Page size |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

---

## 3. Field Inventory

Complete field catalog from the live `?f=json` response (32 fields):

| Field Name | Type | Alias | Currently Mapped? | Maps To |
|------------|------|-------|-------------------|---------|
| FID | OID | FID | NO | -- |
| FEAT_TYPE | String | FEAT_TYPE | NO | -- |
| **CALC_ACRE** | **Double** | CALC_ACRE | **YES** | **`acreage`** |
| PAR_NUM | String | PAR_NUM | NO | -- |
| LOT_NUM | String | LOT_NUM | NO | -- |
| SUBCODE | String | SUBCODE | NO | -- |
| SHAPE_LENG | Double | SHAPE_LENG | NO | -- |
| **ParcelDisp** | **String** | ParcelDisp | **YES** | **`parcel_number`** |
| StrNum | String | StrNum | NO | -- |
| StrName | String | StrName | NO | -- (display only) |
| StSuffix | String | StSuffix | NO | -- |
| SubdCode | String | SubdCode | NO | -- |
| TxDist | Integer | TxDist | NO | -- |
| **PRuse** | **String** | PRuse | **YES** | **`use_type`** |
| PropertyUs | String | PropertyUs | NO | -- (full-description sibling of `PRuse`) |
| BldgCnt | Integer | BldgCnt | NO | -- |
| XtraFeaCnt | Integer | XtraFeaCnt | NO | -- |
| LandCnt | Integer | LandCnt | NO | -- |
| **OwnerName** | **String** | OwnerName | **YES** | **`owner_name`** |
| **Addr1** | **String** | Addr1 | **YES** | **`site_address`** |
| Addr2 | String | Addr2 | NO | -- |
| Addr3 | String | Addr3 | NO | -- |
| City | String | City | NO | -- |
| State | String | State | NO | -- |
| Zip5 | String | Zip5 | NO | -- |
| Zip4 | String | Zip4 | NO | -- |
| Cntry | String | Cntry | NO | -- |
| EZone | String | EZone | NO | -- |
| NumUnits | Integer | NumUnits | NO | -- |
| GlobalID | String | GlobalID | NO | -- |
| Shape__Area | Double | Shape__Area | NO | -- |
| Shape__Length | Double | Shape__Length | NO | -- |

---

## 4. What We Query

### WHERE Clause Pattern

```sql
OwnerName LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases into a single WHERE. Single quotes are escaped by doubling.

### Batching Rules

2000-char WHERE cap. Max record count per page is 2000 (higher than Bay/Escambia).

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 5. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | ParcelDisp | -- |
| `owner_name` | OwnerName | -- |
| `site_address` | Addr1 | Addr2/Addr3 not mapped |
| `use_type` | PRuse | Short code; `PropertyUs` has the longer description |
| `acreage` | CALC_ACRE | PA-computed acreage (Double), no unit conversion needed |
| `geometry` | Shape | Polygons |

---

## 6. Diff vs Okeechobee (ArcGIS Online peer)

Santa Rosa and Okeechobee both ride on the Esri-hosted `services.arcgis.com` infrastructure rather than a county-hosted server, but the schemas differ materially.

| Attribute | Santa Rosa (`Eg4L1xEv2R3abuQd`) | Okeechobee (`jE4lvuOFtdtz6Lbl`, Tyler tenant) |
|-----------|------------------------------------------|-----------------------------------------------|
| Service name | `ParcelsOpenData` | `Tyler_Technologies_Display_Map` |
| Layers at root | 1 (standalone layer) | 18 (0-17, incl. zoning, FLU, FEMA, hydrants) |
| ObjectId field | `FID` | `OBJECTID` |
| Acreage field | `CALC_ACRE` (Double) | `Acerage` (String, sic typo) |
| Owner field | `OwnerName` | `Owner1` (+ unused `Owner2`) |
| Use field | `PRuse` (+ unused `PropertyUs`) | (not present) |
| Spatial reference | WKID 103024 (StatePlane FL North ft) | WKID 102100 (Web Mercator) |
| Capabilities | `Query,Extract` | `Query,Extract,Sync` |
| Hosted by | Esri-hosted county open-data tenant | Tyler Technologies tenant |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | ParcelDisp | Alternate parcel number | PAR_NUM |
| Owner | YES | OwnerName | -- | -- |
| Site address | PARTIAL | Addr1 | Addr2, Addr3, city, state, zip | Addr2, Addr3, City, State, Zip5, Zip4 |
| Street detail | NO | -- | Street number, name, suffix | StrNum, StrName, StSuffix |
| Use | YES | PRuse | Full description | PropertyUs |
| Subdivision code | NO | -- | -- | SubdCode, SUBCODE |
| Lot number | NO | -- | Lot | LOT_NUM |
| Acreage | YES | CALC_ACRE | GIS-computed area | Shape__Area |
| Building count | NO | -- | Buildings per parcel | BldgCnt |
| Extra feature count | NO | -- | -- | XtraFeaCnt |
| Land count | NO | -- | -- | LandCnt |
| Tax district | NO | -- | -- | TxDist |
| Number of units | NO | -- | -- | NumUnits |
| Empire/evacuation zone | NO | -- | -- | EZone |
| Geometry | YES | Shape | Perimeter | Shape__Length |

Of 32 attribute fields, 5 are mapped (parcel, owner, address, use, acreage) plus geometry. Mailing address (Addr2/Addr3 + City/State/Zip), building counts, and the structured subdivision code are all ignored.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion: rings -> GeoJSON Polygon / MultiPolygon via shoelace shell/hole classification.

### Coordinate Re-projection

Source SRS is NAD 1983 (2011) StatePlane Florida North (WKID 103024, latestWkid 6441), units US survey feet. We request `outSR=4326` so the server re-projects to WGS84 before returning coordinates.

### cos²(lat) Correction

Not triggered for Santa Rosa because `CALC_ACRE` is a PA-sourced Double acreage attribute, not `Shape__Area`.

---

## 9. Known Limitations and Quirks

1. **`PRuse` is lowercase-mixed.** The use-code field is literally `PRuse` -- not `PRUSE`, `PRUse`, or `Pr_Use`. ArcGIS field names are case-sensitive here; "correcting" the case breaks the query. A sibling `PropertyUs` field holds the longer description but is not mapped.

2. **`services.arcgis.com` tenant, not county-hosted.** The endpoint lives on ArcGIS Online under the county's public open-data org (`Eg4L1xEv2R3abuQd`). There is no `gis.santarosafl.gov` REST surface exposed to the public for parcels. Refresh cadence is controlled by the open-data publisher, not by the PA directly.

3. **StatePlane FL North (ft) native SRS.** Unlike Bay (same StatePlane) or most FL AGO tenants (Web Mercator), Santa Rosa's stored SRS is NAD 1983 (2011) StatePlane Florida North in US survey feet (WKID 103024). `outSR=4326` gets us to WGS84 server-side.

4. **Capabilities are limited to `Query,Extract`.** No `Sync`, no `Editing`. This is a read-only open-data layer; attempts to apply edits will fail.

5. **ObjectId is `FID`, not `OBJECTID`.** Some Esri tooling defaults to `OBJECTID` and silently mis-paginates if the OID field is named `FID`. Any custom tooling must honor `objectIdField` from the service metadata.

6. **Addr1 is street-only.** Mailing completeness requires concatenating Addr1 + Addr2 + Addr3 + City + State + Zip5(+Zip4) + Cntry. The adapter maps only `Addr1` to `site_address`.

7. **Two use fields: `PRuse` short vs `PropertyUs` long.** The seed config picks `PRuse`. Downstream code comparing against DOR code descriptions must account for this choice.

8. **Max record count 2000.** Higher than Bay (1000) and Escambia (1000). Pagination less frequent on wide sweeps.

9. **Tenant ID `Eg4L1xEv2R3abuQd` is stable.** Esri-hosted org ID; treat as an opaque identifier (do NOT try to infer semantics from the string).

10. **Owner address not in schema.** Addr1/2/3 on this layer are the SITE address (parcel location), not the OWNER mailing address. There is no separate owner-mailing column set -- a known limitation for Santa Rosa BI.

11. **Shape__Area available but unused.** CALC_ACRE is authoritative (PA-sourced). Shape__Area (Double) is GIS-computed and may diverge due to projection / digitization artifacts.

12. **No Tyler tenant coupling.** Unlike Okeechobee's `services3.arcgis.com/jE4lvuOFtdtz6Lbl` (Tyler Technologies org), Santa Rosa's `services.arcgis.com/Eg4L1xEv2R3abuQd` is the county's own AGO tenant and is NOT bound to a permitting platform.

**Source of truth:** `seed_bi_county_config.py` (Santa Rosa block, lines 261-268), `county-registry.yaml` (`santa-rosa-fl.projects.bi`, L348-352), live metadata from `https://services.arcgis.com/Eg4L1xEv2R3abuQd/arcgis/rest/services/ParcelsOpenData/FeatureServer/0?f=json` (probed 2026-04-14, HTTP 200, 13 KB)
