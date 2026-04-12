from __future__ import annotations

from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter


class HernandoCountyAdapter(TylerEnerGovAdapter):
    slug = "hernando-county"
    display_name = "Hernando County"
    base_url = "https://hernandocountyfl-energovweb.tylerhost.net/apps/selfservice"
