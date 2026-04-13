from modules.permits.scrapers.adapters.iworq import IworqAdapter


class PanamaCityBeachAdapter(IworqAdapter):
    slug = "panama-city-beach"
    display_name = "Panama City Beach"
    search_url = "https://panamacitybeach.portal.iworq.net/PANAMACITYBEACH/permits/602"
    referer = "https://www.pcbfl.gov/219/Permit-Inspection-Search"
