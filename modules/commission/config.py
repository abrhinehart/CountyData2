"""Commission module configuration.

Ports the original Commission Radar config for the unified CountyData2 app.
Flask-specific settings have been dropped. Database URL resolution now
defers to the shared ``config.DATABASE_URL`` (Postgres), and paths are
anchored to this module's directory rather than the old standalone repo.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Module root: C:/.../CountyData2/modules/commission
MODULE_ROOT = Path(__file__).resolve().parent
# Project root: C:/.../CountyData2
PROJECT_ROOT = MODULE_ROOT.parents[1]

DEFAULT_PDF_STORAGE_DIR = MODULE_ROOT / "downloaded_agendas"
DEFAULT_CONFIG_DIR = MODULE_ROOT / "config"

# Load env vars from the shared project .env if present. override=True so
# the .env file wins over a stale or empty shell export (e.g. a pre-set
# ANTHROPIC_API_KEY="" from a previous session) — .env is the source of
# truth for secrets in development.
load_dotenv(PROJECT_ROOT / ".env", override=True)


def _normalize_module_path(path_value, default_path: Path) -> str:
    """Return an absolute path anchored to the module root when needed."""
    raw_path = Path(path_value).expanduser() if path_value else default_path
    if not raw_path.is_absolute():
        raw_path = MODULE_ROOT / raw_path
    return str(raw_path.resolve())


def get_module_path(env_name: str, default_path: Path) -> str:
    """Return a module-anchored absolute path for a path-like env variable."""
    return _normalize_module_path(os.getenv(env_name), default_path)


def get_anthropic_api_key(env_value: str | None = None) -> str | None:
    """Return the configured Anthropic API key, or None if unset/blank."""
    if env_value is None:
        env_value = os.getenv("ANTHROPIC_API_KEY")
    if env_value is None:
        return None

    cleaned = env_value.strip()
    return cleaned or None


def require_anthropic_api_key(env_value: str | None = None) -> str:
    """Return the Anthropic API key or raise a clear error before extraction starts."""
    api_key = get_anthropic_api_key(env_value)
    if api_key is None:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is required for extraction. "
            "Set it in the project .env file or your environment before running process/scrape."
        )
    return api_key


def get_scrape_delay_seconds(env_value: str | None = None) -> float:
    """Return the configured inter-download delay in seconds."""
    if env_value is None:
        env_value = os.getenv("SCRAPE_DELAY_SECONDS", "1")

    try:
        delay = float(env_value)
    except ValueError as exc:
        raise RuntimeError("SCRAPE_DELAY_SECONDS must be a number.") from exc

    if delay < 0:
        raise RuntimeError("SCRAPE_DELAY_SECONDS cannot be negative.")

    return delay


# Defer to the shared project DATABASE_URL so every module talks to the same Postgres.
try:
    from config import DATABASE_URL  # type: ignore  # shared project config
except Exception:  # pragma: no cover - fallback for isolated imports
    DATABASE_URL = os.getenv("DATABASE_URL", "")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
PDF_STORAGE_DIR = get_module_path("PDF_STORAGE_DIR", DEFAULT_PDF_STORAGE_DIR)
CONFIG_DIR = get_module_path("CR_CONFIG_DIR", DEFAULT_CONFIG_DIR)
SCRAPE_DELAY_SECONDS = get_scrape_delay_seconds()
