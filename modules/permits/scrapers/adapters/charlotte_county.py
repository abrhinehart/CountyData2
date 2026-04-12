from modules.permits.scrapers.adapters.accela_citizen_access import AccelaCitizenAccessAdapter


class CharlotteCountyAdapter(AccelaCitizenAccessAdapter):
    slug = "charlotte-county"
    display_name = "Charlotte County"
    agency_code = "BOCC"
    target_record_type = ""  # BOCC portal has no record-type dropdown; search all Building permits
    permit_type_filter = ("Residential Single Family",)  # post-search filter for new-construction
    detail_request_delay = 0.5  # BOCC portal rate-limits aggressively
