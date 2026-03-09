import re
import pandas as pd


def split_parties(text: str | float | None, delimiters: list[str] | None = None) -> list[str]:
    """
    Split a multi-party name field into a list of individual party names.
    Splits on newlines first, then on each configured delimiter.
    Returns a flat list of stripped, non-empty names.
    """
    if pd.isna(text) or not text:
        return []
    text = str(text).strip()

    # Split on newlines first
    parts = [p.strip() for p in text.split('\n') if p.strip()]

    if delimiters:
        expanded = []
        for part in parts:
            # Split on each delimiter, keeping the first segment and expanding the rest
            segments = [part]
            for d in delimiters:
                new_segments = []
                for seg in segments:
                    new_segments.extend(seg.split(d))
                segments = new_segments
            expanded.extend(s.strip() for s in segments if s.strip())
        parts = expanded

    return parts


def before_first_delimiter(text: str | float | None, delimiters: list[str] | None = None) -> str:
    if pd.isna(text) or not text:
        return ""
    text = str(text).strip()
    
    if not delimiters:
        return text
    
    positions = [text.find(d) for d in delimiters if text.find(d) >= 0]
    if not positions:
        return text
    return text[:min(positions)].strip()
    

def before_first_newline(text):
    if pd.isna(text):
        return ''
    text = str(text).strip()
    if '\n' in text:
        return text.split('\n', 1)[0].strip()
    return text


def remove_lot_references(text: str) -> str:
    if not text:
        return text
    patterns = [
        r'\bLOT\s*:\s*\d+(?:-\d+)?\b',
        r'\bL\s*:\s*\d+(?:-\d+)?\b',
        r'\bLOT\s*\d+(?:-\d+)?\b',
        r'\bL\s*\d+(?:-\d+)?\b',
        r'\bLT\s*\d{1,4}\b',                    # LT + 1-4 digits
        r'\bLT\s*:\s*\d{1,4}\b',                # LT: + 1-4 digits
        r'\bLOTS?\b\s*',
        r'^LOT\s*:\s*',
        r'^L\s*:\s*',
        r'\bLS\s*\d{1,3}-\d{1,3}\b'   # LS 0-0, LS 12-34, LS 123-456, etc.
    ]
    for pat in patterns:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)
    return text.strip()


def remove_block_references(text: str) -> str:
    if not text:
        return text
    patterns = [
        r'\bBLK\s*:\s*[A-Za-z0-9]+(?:[-][A-Za-z0-9]+)?\b',
        r'\bBLOCK\s*:\s*[A-Za-z0-9]+(?:[-][A-Za-z0-9]+)?\b',
        r'\bBLK\s*[A-Za-z0-9]+(?:[-][A-Za-z0-9]+)?\b',
        r'\bBLOCK\s*[A-Za-z0-9]+(?:[-][A-Za-z0-9]+)?\b',
        r'\bBK\s*\d{1,4}\b',
        r'\bBK\s*:\s*\d{1,4}\b',
        r'\bBK\s*[A-Za-z]\b',                    # BK followed by single letter
        r'\bBK\s*:\s*[A-Za-z]\b',                # BK: followed by single letter
        r'\bBLK\b',
        r'\bBLOCK\b',
    ]
    for pat in patterns:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)
    return text.strip()


def remove_sub_references(text: str) -> str:
    if not text:
        return text
    patterns = [
        r'\bSUB\s*:\s*',
        r'\bSUB\b\s*',
        r'^SUB\s*:\s*',
    ]
    for pat in patterns:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)
    return text.strip()


def extract_phase(text: str, phase_keywords: list[str]) -> str:
    if not text:
        return ""
    
    phase_keywords_str = '|'.join(phase_keywords)
    pattern = rf'(?:{phase_keywords_str})\s*([A-Za-z0-9]+(?:[-]?[A-Za-z])?)'
    
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    if matches:
        return matches[-1].strip()
    
    return ""


def fix_phase_typos(phase: str) -> str:
    if not phase:
        return phase
    
    upper = phase.upper()
    
    roman_map = {
        'I': '1', 'IA': '1A', 'IB': '1B', 'IC': '1C',
        'II': '2', 'III': '3', 'IV': '4', 'V': '5',
        'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9',
        'X': '10', 'XI': '11', 'XII': '12',
        'TWO': '2',
    }
    return roman_map.get(upper, phase)


def remove_phase_from_text(text: str, phase_keywords: list[str]) -> str:
    if not text:
        return text
    phase_keywords_str = '|'.join(phase_keywords)
    pattern = rf'(?:{phase_keywords_str})\s*[A-Za-z0-9]+(?:[-]?[A-Za-z])?\b\s*[,;.]?\s*'
    text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text.strip()


def remove_after_parcel(text: str) -> str:
    if not text:
        return text
    # Remove "Parcel..." and everything after (case-insensitive)
    parts = re.split(r',\s*parcel\b', text, flags=re.IGNORECASE)
    return parts[0].strip()


def remove_after_section(text: str) -> str:
    if not text:
        return text
    # Split on 'Section' (case-insensitive) and keep only before it
    parts = re.split(r'\bsection\b', text, flags=re.IGNORECASE)
    return parts[0].strip()

# this functions isnt very productive. cut it if the program gets too slow.
def remove_unrec(text: str) -> str:
    if not text:
        return text
    return re.sub(r'unrec', '', text, flags=re.IGNORECASE).strip()


def clean_subdivision(subdivision: str, phase_keywords: list[str]) -> str:
    if not subdivision:
        return ""
    
    cleaned = remove_lot_references(subdivision)
    cleaned = remove_block_references(cleaned)
    cleaned = remove_sub_references(cleaned)          # added here for global use
    cleaned = remove_phase_from_text(cleaned, phase_keywords)
    
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'^[,;.]+\s*', '', cleaned).strip()
    cleaned = re.sub(r'\s*[,;.]+$', '', cleaned).strip()
    
    return cleaned

    # FUNCTIONS FOR SPECIFIC COUNTIES

def clean_walton_legal_prefix(df, column_name='legal'):
    if column_name in df.columns:
        df[column_name] = df[column_name].astype(str).str.replace('Legal ', '', regex=False).str.strip()
    return df


def clean_hernando_legal(df, legal_col='Legal'):
    if legal_col in df.columns:
        df[legal_col] = (
            df[legal_col]
            .astype(str)
            .str.replace('L Blk Un Sub', '', regex=False)
            .str.replace('S T R', '', regex=False)
            .str.strip()
        )
    return df


def clean_hernando_subdivision(df, sub_col='Subdivision'):
    if sub_col in df.columns:
        df[sub_col] = (
            df[sub_col]
            .astype(str)
            .str.replace('legalfield_', '', regex=False)
            .str.strip()
        )
    return df


def remove_santarosa_unit(text: str) -> str:
    if not text:
        return text
    # Remove 00/X, 45/D, 88/Q, 38/Y, etc. — anywhere in string
    # \d{1,3}/[A-Z]  → 1 to 3 digits / single uppercase letter
    text = re.sub(r'\b\d{1,3}/[A-Z]\b', '', text, flags=re.IGNORECASE)
    # Also catch with spaces around / (e.g. 45 / D)
    text = re.sub(r'\b\d{1,3}\s*/\s*[A-Z]\b', '', text, flags=re.IGNORECASE)
    return text.strip()

