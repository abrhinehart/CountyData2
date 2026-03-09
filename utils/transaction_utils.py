# utils/transaction_utils.py

def guess_transaction_type(grantee: str | None, company_indicators: list | set) -> str:
    if grantee is None or not str(grantee).strip():
        return "House Sale"

    upper = str(grantee).upper().strip()

    if any(kw.upper() in upper for kw in company_indicators):
        return "Lot Purchase"

    return "House Sale"