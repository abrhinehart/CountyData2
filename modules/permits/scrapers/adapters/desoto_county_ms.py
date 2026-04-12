from __future__ import annotations

from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter


class DeSotoCountyMsAdapter(TylerEnerGovAdapter):
    slug = "desoto-county-ms"
    display_name = "DeSoto County, MS"
    base_url = "https://energovweb.desotocountyms.gov/energov_prod/selfservice"
