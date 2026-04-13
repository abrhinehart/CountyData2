from modules.permits.scrapers.adapters.iworq import IworqAdapter


class LakeHamiltonAdapter(IworqAdapter):
    slug = "lake-hamilton"
    display_name = "Lake Hamilton"
    # NOTE: Research found the landing page at townoflakehamilton.portal.iworq.net/portalhome/townoflakehamilton
    # The permits module URL below follows the standard iWorQ pattern but needs live verification.
    search_url = "https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permits/600"
