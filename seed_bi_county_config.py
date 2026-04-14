"""
seed_bi_county_config.py - Populate the bi_county_config table with GIS endpoint
data extracted from the Builder Inventory county seed file.

Idempotent: safe to run multiple times (uses ON CONFLICT).
Missing counties are created in the shared counties table first.

Usage:
    python seed_bi_county_config.py
"""

import psycopg2

from config import DATABASE_URL

# Every county from BI's seed_counties.py that has a gis_endpoint.
# Florida counties default to state='FL'; out-of-state counties specify their state.
# Fields set to None are stored as NULL in the database.

COUNTY_GIS_CONFIGS = [
    # ── Florida counties (batch 1) ─────────────────────────────────────────────
    {
        "name": "Alachua", "state": "FL",
        "gis_endpoint": "https://services.arcgis.com/cNo3jpluyt69V8Ek/arcgis/rest/services/PublicParcel/FeatureServer/0",
        "gis_owner_field": "Owner_Mail_Name",
        "gis_parcel_field": "Name",
        "gis_address_field": "FULLADDR",
        "gis_use_field": None,
        "gis_acreage_field": "StatedArea",
    },
    {
        "name": "Baker", "state": "FL",
        "gis_endpoint": "https://services6.arcgis.com/HSWu3dhzHf7nZfIa/arcgis/rest/services/parcels_web/FeatureServer/0",
        "gis_owner_field": "Owner",
        "gis_parcel_field": "PIN",
        "gis_address_field": "Site_Addre",
        "gis_use_field": "Use_Descri",
        "gis_acreage_field": "GIS_Acreag",
    },
    {
        "name": "Bay", "state": "FL",
        "gis_endpoint": "https://gis.baycountyfl.gov/arcgis/rest/services/BayView/BayView/MapServer/2",
        "gis_owner_field": "A2OWNAME",
        "gis_parcel_field": "A1RENUM",
        "gis_address_field": "DSITEADDR",
        "gis_use_field": "DORAPPDESC",
        "gis_acreage_field": "DTAXACRES",
    },
    {
        "name": "Brevard", "state": "FL",
        "gis_endpoint": "https://gis.brevardfl.gov/gissrv/rest/services/Base_Map/Parcel_New_WKID2881/MapServer/5",
        "gis_owner_field": "OWNER_NAME1",
        "gis_parcel_field": "PARCEL_ID",
        "gis_address_field": "STREET_NAME",
        "gis_use_field": "USE_CODE",
        "gis_acreage_field": "ACRES",
    },
    {
        "name": "Clay", "state": "FL",
        "gis_endpoint": "https://maps.claycountygov.com/server/rest/services/Parcel/FeatureServer/0",
        "gis_owner_field": "Name",
        "gis_parcel_field": "PIN",
        "gis_address_field": "StreetName",
        "gis_use_field": "Usedesc",
        "gis_acreage_field": "GISACRES",
    },
    {
        "name": "Columbia", "state": "FL",
        "gis_endpoint": "https://gis.columbiacountyfla.com/hosting/rest/services/Parcels/MapServer/1",
        "gis_owner_field": "Owner",
        "gis_parcel_field": "ParcelNo",
        "gis_address_field": "Subdivision",
        "gis_use_field": None,
        "gis_acreage_field": "Acres",
    },
    {
        "name": "DeSoto", "state": "FL",
        "gis_endpoint": "https://services6.arcgis.com/4Zxj9BGpFPVGgwpo/arcgis/rest/services/Parcels_2025/FeatureServer/11",
        "gis_owner_field": "OWNER_NAME",
        "gis_parcel_field": "PIN",
        "gis_address_field": "FULL_ADDR",
        "gis_use_field": None,
        "gis_acreage_field": "ACREAGE",
    },
    {
        "name": "Duval", "state": "FL",
        "gis_endpoint": "https://maps.coj.net/coj/rest/services/CityBiz/Parcels/MapServer/0",
        "gis_owner_field": "LNAMEOWNER",
        "gis_parcel_field": "RE",
        "gis_address_field": "ST_NAME",
        "gis_use_field": "DESCPU",
        "gis_acreage_field": "ACRES",
    },
    {
        "name": "Escambia", "state": "FL",
        "gis_endpoint": "https://gismaps.myescambia.com/arcgis/rest/services/Individual_Layers/parcels/MapServer/0",
        "gis_owner_field": "OWNER",
        "gis_parcel_field": "REFNUM",
        "gis_address_field": "SITEADDR",
        "gis_use_field": "LANDTYPE",
        "gis_acreage_field": "LANDSIZE",
    },
    {
        "name": "Flagler", "state": "FL",
        "gis_endpoint": "https://services3.arcgis.com/hSKL9bYjhP4rHxSD/arcgis/rest/services/Flagler_County_Parcels/FeatureServer/0",
        "gis_owner_field": "file_as_name",
        "gis_parcel_field": "PARCELNO",
        "gis_address_field": "situs_street",
        "gis_use_field": "property_use_desc",
        "gis_acreage_field": "legal_acreage",
    },
    {
        "name": "Hardee", "state": "FL",
        "gis_endpoint": "https://gis.hardeecounty.net/arcgis/rest/services/InfoMap/MapServer/5",
        "gis_owner_field": "OWNNAME",
        "gis_parcel_field": "PIN_DSP",
        "gis_address_field": "STREET",
        "gis_use_field": None,
        "gis_acreage_field": "TOTACRES",
    },
    {
        "name": "Hendry", "state": "FL",
        "gis_endpoint": "https://services7.arcgis.com/8l7Qq5t0CPLAJwJK/arcgis/rest/services/Hendry_County_Parcels/FeatureServer/0",
        "gis_owner_field": "OWNAME",
        "gis_parcel_field": "PARCELNO",
        "gis_address_field": "LOCADD",
        "gis_use_field": None,
        "gis_acreage_field": None,
    },
    {
        "name": "Hillsborough", "state": "FL",
        "gis_endpoint": "https://gis.hcpafl.org/arcgis/rest/services/Webmaps/HillsboroughFL_WebParcels/MapServer/0",
        "gis_owner_field": "Owner1",
        "gis_parcel_field": "folio",
        "gis_address_field": "FullAddress",
        "gis_use_field": "Homestead",
        "gis_acreage_field": None,
    },
    {
        "name": "Lake", "state": "FL",
        "gis_endpoint": "https://gis.lakecountyfl.gov/lakegis/rest/services/PropertyAppraiser/FieldMap/MapServer/0",
        "gis_owner_field": "OwnerName",
        "gis_parcel_field": "ParcelNumber",
        "gis_address_field": "PropertyAddress",
        "gis_use_field": "LandUseDescription",
        "gis_acreage_field": "Acres",
    },
    {
        "name": "Lee", "state": "FL",
        "gis_endpoint": "https://gissvr.leepa.org/gissvr/rest/services/ParcelRoads2/MapServer/12",
        "gis_owner_field": "OwnerName",
        "gis_parcel_field": "Name",
        "gis_address_field": "Address1",
        "gis_use_field": "LandUseDesc",
        "gis_acreage_field": "PlatAcres",
    },
    {
        "name": "Leon", "state": "FL",
        "gis_endpoint": "https://intervector.leoncountyfl.gov/intervector/rest/services/MapServices/TLC_OverlayParnal_D_WM/MapServer/0",
        "gis_owner_field": "OWNER1",
        "gis_parcel_field": "TAXID",
        "gis_address_field": "SITEADDR",
        "gis_use_field": "PROP_USE",
        "gis_acreage_field": "CALC_ACREA",
    },
    {
        "name": "Levy", "state": "FL",
        "gis_endpoint": "https://www45.swfwmd.state.fl.us/arcgis12/rest/services/BaseVector/parcel_search/MapServer/9",
        "gis_owner_field": "OWNERNAME",
        "gis_parcel_field": "PARCELID",
        "gis_address_field": "SITUSADD1",
        "gis_use_field": "DORUSECODE",
        "gis_acreage_field": None,
    },
    {
        "name": "Manatee", "state": "FL",
        "gis_endpoint": "https://www.mymanatee.org/gisits/rest/services/commonoperational/parcels_pl_only/FeatureServer/0",
        "gis_owner_field": "OWNER",
        "gis_parcel_field": "PARCEL_ID",
        "gis_address_field": "PRIMARY_ADDRESS",
        "gis_use_field": "LUC_DESCRIPTION",
        "gis_acreage_field": "ACRES",
    },
    {
        "name": "Marion", "state": "FL",
        "gis_endpoint": "https://gis.marionfl.org/public/rest/services/General/Parcels/MapServer/0",
        "gis_owner_field": "NAME",
        "gis_parcel_field": "PARCEL",
        "gis_address_field": "SITUS_1",
        "gis_use_field": "FIC",
        "gis_acreage_field": "ACRES",
    },
    {
        "name": "Nassau", "state": "FL",
        "gis_endpoint": "https://maps.ncpafl.com/ncflpa_arcgis/rest/services/nassau/NassauCountyPublicTaxMap/MapServer/144",
        "gis_owner_field": "Name",
        "gis_parcel_field": "PIN",
        "gis_address_field": "Situs_full",
        "gis_use_field": "parcel_use_cd",
        "gis_acreage_field": "DeedAcre",
    },
    {
        "name": "Okaloosa", "state": "FL",
        "gis_endpoint": "https://gis.myokaloosa.com/arcgis/rest/services/BaseMap_Layers/MapServer/111",
        "gis_owner_field": "PATPCL_OWNER",
        "gis_parcel_field": "PATPCL_PIN",
        "gis_address_field": "PATPCL_ADDR1",
        "gis_use_field": "PATPCL_USEDESC",
        "gis_acreage_field": "PATPCL_LGL_ACRE",
    },
    {
        "name": "Orange", "state": "FL",
        "gis_endpoint": "https://ocgis4.ocfl.net/arcgis/rest/services/Public_Dynamic/MapServer/216",
        "gis_owner_field": "NAME1",
        "gis_parcel_field": "PARCEL",
        "gis_address_field": "SITUS",
        "gis_use_field": "DOR_CODE",
        "gis_acreage_field": "ACREAGE",
    },
    {
        "name": "Pasco", "state": "FL",
        "gis_endpoint": "https://pascogis.pascocountyfl.net/giswebs/rest/services/PascoMapper/Parcels/MapServer/7",
        "gis_owner_field": "OWNER_NAME_1",
        "gis_parcel_field": "VPARCEL",
        "gis_address_field": "SITE_ADDRESS",
        "gis_use_field": "LAND_USE_DESC",
        "gis_acreage_field": "SITE_ACRES",
    },
    {
        "name": "Pinellas", "state": "FL",
        "gis_endpoint": "https://egis.pinellas.gov/gis/rest/services/AGO/Parcels/MapServer/0",
        "gis_owner_field": "PGIS.PGIS.PAOGENERAL.OWNER1",
        "gis_parcel_field": "PGIS.PGIS.ParcelsPublic.PARCELNO",
        "gis_address_field": "PGIS.PGIS.PAOGENERAL.SITE_ST",
        "gis_use_field": "PGIS.PGIS.PAOGENERAL.USE_CODE",
        "gis_acreage_field": "PGIS.PGIS.ParcelsPublic.STATEDAREA",
    },
    {
        "name": "Polk", "state": "FL",
        "gis_endpoint": "https://gis.polk-county.net/server/rest/services/Map_Property_Appraiser/FeatureServer/1",
        "gis_owner_field": "NAME",
        "gis_parcel_field": "PARCELID",
        "gis_address_field": "PROP_ADRSTR",
        "gis_use_field": "DOR_USE_CODE_DESC",
        "gis_acreage_field": "TOT_ACREAGE",
        "gis_subdivision_field": "SUBDIVISION",
        "gis_building_value_field": "TOT_BLD_VAL",
        "gis_appraised_value_field": "ASSESSVAL",
        "gis_deed_date_field": "DEED_DT",
    },
    {
        "name": "Putnam", "state": "FL",
        "gis_endpoint": "https://pamap.putnam-fl.gov/server/rest/services/CadastralData/FeatureServer/2",
        "gis_owner_field": "OWNERNME1",
        "gis_parcel_field": "PARCELID",
        "gis_address_field": "SITEADDRESS",
        "gis_use_field": "USEDSCRP",
        "gis_acreage_field": "STATEDAREA",
    },
    {
        "name": "Santa Rosa", "state": "FL",
        "gis_endpoint": "https://services.arcgis.com/Eg4L1xEv2R3abuQd/arcgis/rest/services/ParcelsOpenData/FeatureServer/0",
        "gis_owner_field": "OwnerName",
        "gis_parcel_field": "ParcelDisp",
        "gis_address_field": "Addr1",
        "gis_use_field": "PRuse",
        "gis_acreage_field": "CALC_ACRE",
    },
    {
        "name": "Sarasota", "state": "FL",
        "gis_endpoint": "https://services3.arcgis.com/icrWMv7eBkctFu1f/arcgis/rest/services/ParcelHosted/FeatureServer/0",
        "gis_owner_field": "NAME1",
        "gis_parcel_field": "ID",
        "gis_address_field": "FULLADDRESS",
        "gis_use_field": "STCD",
        "gis_acreage_field": "MeasuredAcreage",
    },
    {
        "name": "Seminole", "state": "FL",
        "gis_endpoint": "https://utility.arcgis.com/usrsvcs/servers/9b9c9fd45bdc4c39a2bd518da39d1e1c/rest/services/InformationKiosk/MapServer/1",
        "gis_owner_field": "OwnerName",
        "gis_parcel_field": "ParcelNumber",
        "gis_address_field": "PropertyAddress",
        "gis_use_field": "DOR",
        "gis_acreage_field": "GISAcres",
    },
    {
        "name": "St. Johns", "state": "FL",
        "gis_endpoint": "https://www.gis.sjcfl.us/sjcgis/rest/services/Parcel/MapServer/0",
        "gis_owner_field": "PRP_NAME",
        "gis_parcel_field": "PIN",
        "gis_address_field": "PRP_ADDR",
        "gis_use_field": "USE_DESC",
        "gis_acreage_field": "Shape.STArea()",
    },
    {
        "name": "Suwannee", "state": "FL",
        "gis_endpoint": "https://services6.arcgis.com/B8iKcMs83hgqommE/arcgis/rest/services/Parcels_Suwannee_2024/FeatureServer/0",
        "gis_owner_field": "OWNNAME",
        "gis_parcel_field": "PARCELID",
        "gis_address_field": "SITEADD",
        "gis_use_field": "PARUSEDESC",
        "gis_acreage_field": "ACRES",
    },
    {
        "name": "Volusia", "state": "FL",
        "gis_endpoint": "https://maps2.vcgov.org/arcgis/rest/services/MapIT/MapServer/5",
        "gis_owner_field": "OWNER1",
        "gis_parcel_field": "DORPID",
        "gis_address_field": "ADDRFULL",
        "gis_use_field": "PC",
        "gis_acreage_field": "CALCACRES",
    },
    # ── Florida counties (batch 2) ─────────────────────────────────────────────
    {
        "name": "Broward", "state": "FL",
        "gis_endpoint": "https://services.arcgis.com/JMAJrTsHNLrSsWf5/arcgis/rest/services/PARCEL_POLY_BCPA_TAXROLL/FeatureServer/0",
        "gis_owner_field": "NAME_LINE_1",
        "gis_parcel_field": "FOLIO",
        "gis_address_field": "SITUS_STREET_NAME",
        "gis_use_field": "USE_CODE",
        "gis_acreage_field": "GIS_SQUARE_FOOT",
    },
    {
        "name": "Charlotte", "state": "FL",
        "gis_endpoint": "https://agis3.charlottecountyfl.gov/arcgis/rest/services/Essentials/CCGISLayers/MapServer/27",
        "gis_owner_field": "ownersname",
        "gis_parcel_field": "ACCOUNT",
        "gis_address_field": "FullPropertyAddress",
        "gis_use_field": "landuse",
        "gis_acreage_field": "Shape.STArea()",
    },
    {
        "name": "Collier", "state": "FL",
        "gis_endpoint": "https://gmdcmgis.colliercountyfl.gov/server/rest/services/Parcels/MapServer/0",
        "gis_owner_field": "OwnerLine1",
        "gis_parcel_field": "Folio",
        "gis_address_field": "SiteStreetAddress",
        "gis_use_field": "UseCode",
        "gis_acreage_field": "TotalAcres",
    },
    {
        "name": "Hernando", "state": "FL",
        "gis_endpoint": "https://services2.arcgis.com/x5zvhhxfUuRDntRe/arcgis/rest/services/Parcels/FeatureServer/0",
        "gis_owner_field": "OWNER_NAME",
        "gis_parcel_field": "PARCEL_NUMBER",
        "gis_address_field": "SITUS_ADDRESS",
        "gis_use_field": "CER_DOR_CODE",
        "gis_acreage_field": "ACRES",
    },
    {
        "name": "Indian River", "state": "FL",
        "gis_endpoint": "https://services9.arcgis.com/M0DpVhTwTZ42jNsw/arcgis/rest/services/IRCPA_Parcels/FeatureServer/0",
        "gis_owner_field": "OWNER_NAME",
        "gis_parcel_field": "PP_PIN",
        "gis_address_field": "SITE_ADDR",
        "gis_use_field": "DOR_DESC",
        "gis_acreage_field": "LAND_ACRES",
    },
    {
        "name": "Martin", "state": "FL",
        "gis_endpoint": "https://geoweb.martin.fl.us/arcgis/rest/services/Administrative_Areas/base_map/MapServer/10",
        "gis_owner_field": "OWNER",
        "gis_parcel_field": "PCN",
        "gis_address_field": "SITUS_STREET",
        "gis_use_field": "DOR_CODE",
        "gis_acreage_field": "AREA_ACRES",
    },
    {
        "name": "Miami-Dade", "state": "FL",
        "gis_endpoint": "https://gis.miamidade.gov/arcgis/rest/services/MD_LandInformation/MapServer/26",
        "gis_owner_field": "TRUE_OWNER1",
        "gis_parcel_field": "FOLIO",
        "gis_address_field": "TRUE_SITE_ADDR",
        "gis_use_field": "DOR_CODE_CUR",
        "gis_acreage_field": "LOT_SIZE",
    },
    {
        "name": "Okeechobee", "state": "FL",
        "gis_endpoint": "https://services3.arcgis.com/jE4lvuOFtdtz6Lbl/arcgis/rest/services/Tyler_Technologies_Display_Map/FeatureServer/2",
        "gis_owner_field": "Owner1",
        "gis_parcel_field": "ParcelID",
        "gis_address_field": "StreetName",
        "gis_use_field": None,
        "gis_acreage_field": "Acerage",
    },
    {
        "name": "Osceola", "state": "FL",
        "gis_endpoint": "https://gis.osceola.org/hosting/rest/services/Parcels/FeatureServer/3",
        "gis_owner_field": "Owner1",
        "gis_parcel_field": "PARCELNO",
        "gis_address_field": "StreetName",
        "gis_use_field": "DORDesc",
        "gis_acreage_field": "TotalAcres",
    },
    {
        "name": "Palm Beach", "state": "FL",
        "gis_endpoint": "https://gis.pbcgov.org/arcgis/rest/services/Parcels/PARCEL_INFO/FeatureServer/4",
        "gis_owner_field": "OWNER_NAME1",
        "gis_parcel_field": "PARCEL_NUMBER",
        "gis_address_field": "SITE_ADDR_STR",
        "gis_use_field": "PROPERTY_USE",
        "gis_acreage_field": "ACRES",
    },
    {
        "name": "St. Lucie", "state": "FL",
        "gis_endpoint": "https://services1.arcgis.com/oDRzuf2MGmdEHAbQ/arcgis/rest/services/ParcelBoundaries/FeatureServer/0",
        "gis_owner_field": "Owner1",
        "gis_parcel_field": "Parcel_Num",
        "gis_address_field": "SiteAddres",
        "gis_use_field": "LandUseDes",
        "gis_acreage_field": "Acre",
    },
    {
        "name": "Sumter", "state": "FL",
        "gis_endpoint": "https://gis.sumtercountyfl.gov/sumtergis/rest/services/DevelopmentServices/DevServices_Parcel2/MapServer/0",
        "gis_owner_field": "Owners_Nam",
        "gis_parcel_field": "PIN",
        "gis_address_field": "Physical_A",
        "gis_use_field": "PROP_USE_D",
        "gis_acreage_field": "Acres_Lot_",
    },
    # ── Alabama counties ───────────────────────────────────────────────────────
    {
        "name": "Madison", "state": "AL",
        "gis_endpoint": "https://web3.kcsgis.com/kcsgis/rest/services/Madison/Madison_Public_ISV/MapServer/185",
        "gis_owner_field": "PropertyOwner",
        "gis_parcel_field": "ParcelNum",
        "gis_address_field": "PropertyAddress",
        "gis_use_field": None,
        "gis_acreage_field": "Acres",
        "gis_subdivision_field": "Subdivision",
        "gis_building_value_field": "TotalBuildingValue",
        "gis_appraised_value_field": "TotalAppraisedValue",
        "gis_deed_date_field": "DeedDate",
        "gis_previous_owner_field": "PreviousOwners",
        "gis_max_records": 2000,
    },
    {
        "name": "Jefferson", "state": "AL",
        "gis_endpoint": "https://jccgis.jccal.org/server/rest/services/Basemap/Parcels/MapServer/0",
        "gis_owner_field": "OWNERNAME",
        "gis_parcel_field": "PARCELID",
        "gis_address_field": "ADDR_APR",
        "gis_use_field": "Cls",
        "gis_acreage_field": "ACRES_APR",
        "gis_subdivision_field": "SUBDIV_NAME",
        "gis_building_value_field": None,
        "gis_appraised_value_field": "AssdValue",
        "gis_deed_date_field": None,
        "gis_previous_owner_field": None,
        "gis_max_records": 2000,
    },
    {
        "name": "Baldwin", "state": "AL",
        "gis_endpoint": "https://utility.arcgis.com/usrsvcs/servers/c6d99b6b381f4851be35a045e2adb7a8/rest/services/Baldwin/Permitting_MS/MapServer/75",
        "gis_owner_field": "Owner",
        "gis_parcel_field": "PARCELID",
        "gis_address_field": "Full_Address",
        "gis_use_field": "PropertyClass",
        "gis_acreage_field": "CalcAcres",
        "gis_subdivision_field": "Subdivision",
        "gis_building_value_field": "CImpValue",
        "gis_appraised_value_field": "CLandValue",
        "gis_deed_date_field": "DeedRecorded",
        "gis_previous_owner_field": "PreviousOwner",
        "gis_max_records": 10000,
    },
    {
        "name": "Montgomery", "state": "AL",
        "gis_endpoint": "https://gis.montgomeryal.gov/server/rest/services/Parcels/FeatureServer/0",
        "gis_owner_field": "OwnerName",
        "gis_parcel_field": "ParcelNo",
        "gis_address_field": "PropertyAddr1",
        "gis_use_field": "AssessmentClass",
        "gis_acreage_field": "Calc_Acre",
        "gis_subdivision_field": "SubDiv1",
        "gis_building_value_field": "TotalImpValue",
        "gis_appraised_value_field": "TotalValue",
        "gis_deed_date_field": "InstDate",
        "gis_previous_owner_field": None,
        "gis_max_records": 2000,
    },
]

# Column names in bi_county_config that we populate from the config dicts above.
GIS_COLUMNS = [
    "gis_endpoint",
    "gis_owner_field",
    "gis_parcel_field",
    "gis_address_field",
    "gis_use_field",
    "gis_acreage_field",
    "gis_subdivision_field",
    "gis_building_value_field",
    "gis_appraised_value_field",
    "gis_deed_date_field",
    "gis_previous_owner_field",
    "gis_max_records",
]


def ensure_county(cur, name: str, state: str) -> int:
    """Look up or insert a county in the shared counties table. Returns county_id."""
    cur.execute(
        "SELECT id FROM counties WHERE name = %s AND state = %s",
        (name, state),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        """
        INSERT INTO counties (name, state)
        VALUES (%s, %s)
        ON CONFLICT (name, state) DO NOTHING
        RETURNING id
        """,
        (name, state),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # Race condition fallback: another process inserted between SELECT and INSERT.
    cur.execute(
        "SELECT id FROM counties WHERE name = %s AND state = %s",
        (name, state),
    )
    return cur.fetchone()[0]


def seed_bi_county_config(conn):
    """Upsert every county GIS config into bi_county_config."""
    upserted = 0
    created_counties = 0

    with conn.cursor() as cur:
        for cfg in COUNTY_GIS_CONFIGS:
            name = cfg["name"]
            state = cfg["state"]

            # Check if the county existed before we touch it.
            cur.execute(
                "SELECT id FROM counties WHERE name = %s AND state = %s",
                (name, state),
            )
            existed = cur.fetchone() is not None

            county_id = ensure_county(cur, name, state)
            if not existed:
                created_counties += 1
                print(f"  created county: {name}, {state}")

            # Build the values for the upsert.
            values = [cfg.get(col) for col in GIS_COLUMNS]

            set_clause = ", ".join(
                f"{col} = EXCLUDED.{col}" for col in GIS_COLUMNS
            )

            col_names = ", ".join(["county_id"] + GIS_COLUMNS)
            placeholders = ", ".join(["%s"] * (1 + len(GIS_COLUMNS)))

            cur.execute(
                f"""
                INSERT INTO bi_county_config ({col_names})
                VALUES ({placeholders})
                ON CONFLICT (county_id) DO UPDATE
                    SET {set_clause}, updated_at = NOW()
                """,
                [county_id] + values,
            )
            upserted += 1

    conn.commit()
    print(
        f"\nbi_county_config: {upserted} rows upserted"
        f" ({created_counties} new counties created)."
    )


def main():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        seed_bi_county_config(conn)
    finally:
        conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
