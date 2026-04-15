from modules.permits.scrapers.adapters.accela_citizen_access import AccelaCitizenAccessAdapter


class PolkCountyAdapter(AccelaCitizenAccessAdapter):
    slug = "polk-county"
    display_name = "Polk County"
    agency_code = "POLKCO"
    module_name = "Building"
    # Primary record type retained for back-compat callers / tests.
    target_record_type = "Building/Residential/New/NA"
    # ACCELA-01: Curated 9-type subset of the 27 ddlGSPermitType values exposed
    # by POLKCO's Building module.  Scope = residential + commercial-new +
    # 5 single-trade permits + pool.  Excludes: sign permits, mobile-home
    # variants, demolition, contractor licensing renewals, fence/wall, gas,
    # window/door, accessory MH skirting, search-request / pre-permit /
    # admin / temporary-use.  Recon: tmp/dropdown_recon (Wave 1, 2026-04-15).
    target_record_types = (
        "Building/Residential/New/NA",
        "Building/Residential/Renovation/NA",
        "Building/Residential/Accessory/NA",
        "Building/Commercial/New/NA",
        "Building/Trades/Re-Roof/NA",
        "Building/Trades/Electrical/NA",
        "Building/Trades/Plumbing/NA",
        "Building/Trades/Mechanical/NA",
        "Building/Trades/Pool/NA",
    )
    inspections_on_separate_tab = True
