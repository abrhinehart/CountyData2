"""Live validation harness for Commission Radar scrapers.

Reads a jurisdiction YAML, runs fetch_listings + download_document against
the live portal, and prints a terse recon summary. No DB writes, no Claude
extraction. Intended for activating jurisdictions via smoke-test only.

Usage:
    .venv/Scripts/python.exe scripts/cr_live_validate.py <yaml_path> [start] [end]

Dates default to 2025-10-01 .. 2026-04-14 (6-month window).
"""
from __future__ import annotations

import json
import sys
import tempfile
import traceback
from pathlib import Path

import yaml

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.commission.scrapers.base import PlatformScraper  # noqa: E402


MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "html": b"<",  # loose; we check for <html / <!DOC below
    "docx": b"PK",
}


def sniff_format(path: Path, expected: str) -> tuple[bool, str]:
    """Check magic bytes / first chunk matches expected format. Returns (ok, note)."""
    try:
        head = path.read_bytes()[:2048]
    except OSError as exc:
        return False, f"read error: {exc}"
    if expected == "pdf":
        return head.startswith(b"%PDF-"), f"head={head[:8]!r}"
    if expected == "html":
        low = head.lower()
        ok = b"<html" in low or b"<!doctype" in low or b"<body" in low
        return ok, f"html-ish={ok}"
    if expected == "docx":
        return head.startswith(b"PK"), f"head={head[:4]!r}"
    return True, "no sniffer"


def validate(yaml_path: Path, start_date: str, end_date: str) -> dict:
    cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    scraping = cfg.get("scraping", {})
    platform = scraping.get("platform")
    slug = cfg.get("slug", yaml_path.stem)

    result = {
        "slug": slug,
        "platform": platform,
        "yaml": str(yaml_path),
        "start": start_date,
        "end": end_date,
        "listings_count": 0,
        "agenda_count": 0,
        "first_three": [],
        "download": None,
        "status": "FAIL",
        "error": None,
    }

    try:
        scraper = PlatformScraper.for_platform(platform)
    except Exception as exc:
        result["error"] = f"factory: {exc}"
        return result

    try:
        listings = scraper.fetch_listings(scraping, start_date, end_date)
    except Exception:
        result["error"] = "fetch_listings traceback:\n" + traceback.format_exc()
        return result

    result["listings_count"] = len(listings)
    agendas = [l for l in listings if l.document_type == "agenda"]
    result["agenda_count"] = len(agendas)
    result["first_three"] = [
        {"title": l.title[:80], "date": l.date_str, "type": l.document_type,
         "fmt": l.file_format, "url": l.url}
        for l in listings[:3]
    ]

    if not listings:
        result["error"] = "no listings returned"
        return result

    if not agendas:
        result["error"] = "no agenda listings"
        result["status"] = "PARTIAL"
        return result

    # Download smoke
    target = agendas[0]
    with tempfile.TemporaryDirectory() as tmp:
        try:
            path = scraper.download_document(target, tmp)
            p = Path(path)
            size = p.stat().st_size
            ok_fmt, note = sniff_format(p, target.file_format)
            result["download"] = {
                "url": target.url,
                "size_bytes": size,
                "format_ok": ok_fmt,
                "sniff": note,
                "size_ge_1kb": size >= 1024,
            }
            if size >= 1024 and ok_fmt:
                result["status"] = "PASS"
            else:
                result["status"] = "PARTIAL"
                result["error"] = f"download small/bad format (size={size}, {note})"
        except Exception:
            result["status"] = "PARTIAL"
            result["error"] = "download traceback:\n" + traceback.format_exc()

    return result


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: cr_live_validate.py <yaml_path> [start] [end]")
        return 2
    yaml_path = Path(argv[1])
    start = argv[2] if len(argv) > 2 else "2025-10-01"
    end = argv[3] if len(argv) > 3 else "2026-04-14"
    result = validate(yaml_path, start, end)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
