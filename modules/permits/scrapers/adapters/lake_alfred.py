from modules.permits.scrapers.adapters.accela_citizen_access import AccelaCitizenAccessAdapter


class LakeAlfredAdapter(AccelaCitizenAccessAdapter):
    slug = "lake-alfred"
    display_name = "Lake Alfred"
    agency_code = "COLA"
    module_name = "Building"
    target_record_type = "Building/Residential/New/NA"
