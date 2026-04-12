from __future__ import annotations

from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter


class MarionCountyAdapter(TylerEnerGovAdapter):
    slug = "marion-county"
    display_name = "Marion County"
    base_url = "https://selfservice.marionfl.org/energov_prod/selfservice"
