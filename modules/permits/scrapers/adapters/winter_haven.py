from modules.permits.scrapers.adapters.accela_citizen_access import AccelaCitizenAccessAdapter


class WinterHavenAdapter(AccelaCitizenAccessAdapter):
    slug = "winter-haven"
    display_name = "Winter Haven"
    agency_code = "COWH"
    module_name = "Building"
    target_record_type = "Building/Residential/New/NA"
    # NOTE: The COWH Accela portal requires authentication to access the
    # Building module search.  This adapter will return 0 permits until
    # auth support is added to AccelaCitizenAccessAdapter or an
    # alternative data source is found.
