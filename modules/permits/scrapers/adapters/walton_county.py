from __future__ import annotations

from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter


class WaltonCountyAdapter(TylerEnerGovAdapter):
    slug = "walton-county"
    display_name = "Walton County"
    base_url = "https://waltoncountyfl-energovweb.tylerhost.net/apps/SelfService"
