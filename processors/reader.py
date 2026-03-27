from pathlib import Path

import pandas as pd

from config import SUPPORTED_ENCODINGS, SUPPORTED_EXTENSIONS


def read_county_files(county: str, config: dict) -> list[tuple[Path, pd.DataFrame]]:
    """
    Find and read all source files for a county.
    Returns a list of (file_path, DataFrame) tuples.
    All columns are read as strings.
    """
    input_folder = Path(config['input_folder'])
    skiprows = config.get('skiprows', 0)

    files = [
        f
        for ext in SUPPORTED_EXTENSIONS
        for f in input_folder.glob(f"*{ext}")
        if not f.name.startswith('~$')
    ]
    results = []

    for file_path in files:
        df = _read_file(file_path, skiprows, county)
        if df is not None and not df.empty:
            results.append((file_path, df))

    return results


def _read_file(file_path: Path, skiprows: int, county: str) -> pd.DataFrame | None:
    if file_path.suffix in ('.xls', '.xlsx'):
        try:
            return pd.read_excel(file_path, skiprows=skiprows, dtype=str)
        except Exception as e:
            print(f"  [{county}] Could not read {file_path.name}: {e}")
            return None

    for enc in SUPPORTED_ENCODINGS:
        try:
            return pd.read_csv(file_path, skiprows=skiprows, dtype=str, encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  [{county}] Could not read {file_path.name}: {e}")
            return None

    print(f"  [{county}] No valid encoding found for {file_path.name}")
    return None
