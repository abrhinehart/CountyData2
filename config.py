import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load env vars from the project .env. override=True so the .env file wins
# over a stale or empty shell export (e.g. a pre-set POSTGRES_PASSWORD=""
# from a previous session) — .env is the source of truth for secrets in
# development.
_PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(_PROJECT_ROOT / ".env", override=True)


def _build_database_url() -> str:
    raw_url = os.getenv('DATABASE_URL', '').strip()
    parsed = urlparse(raw_url)

    if parsed.scheme in {'postgres', 'postgresql'} and parsed.hostname and parsed.path not in {'', '/'}:
        if parsed.scheme == 'postgres':
            return raw_url.replace('postgres://', 'postgresql://', 1)
        return raw_url

    user = os.getenv('POSTGRES_USER', 'etl_user')
    password = os.getenv('POSTGRES_PASSWORD', 'changeme')
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    database = os.getenv('POSTGRES_DB', 'County-Data')
    return f'postgresql://{user}:{password}@{host}:{port}/{database}'


DATABASE_URL = _build_database_url()

OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', 'Z:/Shared/_Office_Shared/Adam/Code/Format/County Data/Output'))

SUPPORTED_ENCODINGS = ['utf-8', 'cp1252', 'latin1', 'iso-8859-1', 'utf-16', 'cp1250']

SUPPORTED_EXTENSIONS = ['.csv', '.xls', '.xlsx']

COMPANY_KEYWORDS = ['INC', 'LLC', 'HOMES', 'COMPANY', 'INVESTMENTS', 'LTD']
