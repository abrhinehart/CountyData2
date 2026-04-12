from __future__ import annotations

from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter


class OkeechobeeAdapter(TylerEnerGovAdapter):
    slug = "okeechobee"
    display_name = "Okeechobee County"
    base_url = "https://okeechobeecountyfl-energovweb.tylerhost.net/apps/selfservice"
