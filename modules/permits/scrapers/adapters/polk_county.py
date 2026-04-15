from modules.permits.scrapers.adapters.accela_citizen_access import AccelaCitizenAccessAdapter


class PolkCountyAdapter(AccelaCitizenAccessAdapter):
    slug = "polk-county"
    display_name = "Polk County"
    agency_code = "POLKCO"
    module_name = "Building"
    target_record_type = "Building/Residential/New/NA"
    inspections_on_separate_tab = True
