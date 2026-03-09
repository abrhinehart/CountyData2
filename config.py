import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://etl_user:changeme@localhost:5432/County-Data')

OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', 'Z:/Shared/_Office_Shared/Adam/Code/Format/County Data/Output'))

SUPPORTED_ENCODINGS = ['utf-8', 'cp1252', 'latin1', 'iso-8859-1', 'utf-16', 'cp1250']

SUPPORTED_EXTENSIONS = ['.csv', '.xls', '.xlsx']

COMPANY_KEYWORDS = ['INC', 'LLC', 'HOMES', 'COMPANY', 'INVESTMENTS', 'LTD']
