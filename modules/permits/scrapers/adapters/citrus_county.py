from modules.permits.scrapers.adapters.accela_citizen_access import AccelaCitizenAccessAdapter


class CitrusCountyAdapter(AccelaCitizenAccessAdapter):
    slug = "citrus-county"
    display_name = "Citrus County"
    agency_code = "CITRUS"
    module_name = "Building"
    target_record_type = "Building/Residential/NA/NA"
    inspections_on_separate_tab = True
