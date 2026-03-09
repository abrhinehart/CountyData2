from datetime import date, datetime

import pandas as pd


_DATE_FORMATS = ['%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%d-%b-%Y', '%b %d %Y']


def parse_date(value) -> date | None:
    """
    Parse a raw date value from a source file into a Python date object.
    Returns None if the value is empty or cannot be parsed.
    """
    if pd.isna(value) or value == '':
        return None

    if isinstance(value, (datetime, pd.Timestamp)):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text.split()[0], fmt).date()
        except ValueError:
            continue

    return None
