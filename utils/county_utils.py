def normalize_county_key(name: str | None) -> str:
    if not name:
        return ''
    return ''.join(ch for ch in str(name).upper() if ch.isalnum())
