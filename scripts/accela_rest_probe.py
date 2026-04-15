"""Probe Accela v4 REST API availability for our registered Citizen App.

Reads ACCELA_APP_ID (required) and ACCELA_APP_SECRET (optional) from
the environment or .env. Tries each v4 endpoint against a target agency
with up to three auth patterns, records the outcome, and dumps a
compatibility matrix as markdown to stdout (or --out file).

Auth patterns tried, in order:
  1. anonymous   — just `x-accela-appid` + `x-accela-agency` headers
  2. app-creds   — OAuth2 client_credentials → bearer token

This script does not do anything destructive — only GETs and an
exploratory POST /v4/search/records with a single altId filter.

Usage:
  python scripts/accela_rest_probe.py --agency POLKCO --permit BR-2026-2894

Exit code is always 0 unless the App ID itself is missing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.environ.get("ACCELA_APP_ID")
APP_SECRET = os.environ.get("ACCELA_APP_SECRET")

if not APP_ID:
    print("ERROR: ACCELA_APP_ID not set in environment or .env", file=sys.stderr)
    sys.exit(1)

API_BASE = "https://apis.accela.com"
USER_AGENT = "CountyData2-AccelaProbe/1.0"
REQUEST_TIMEOUT = 20


# ── Endpoint catalog ──────────────────────────────────────────────────
# (method, path_template, label, requires_record_id, body_builder_or_None)
# path_template uses {id} for the Accela internal record ID.

ENDPOINTS: list[tuple[str, str, str, bool, Any]] = [
    # Entry-point search: finds internal record ID from altId (human permit #)
    ("POST", "/v4/search/records", "search-records", False, "search_body"),
    # Per-record reads (require internal record ID)
    ("GET",  "/v4/records/{id}",                 "record-detail",  True, None),
    ("GET",  "/v4/records/{id}/addresses",       "addresses",      True, None),
    ("GET",  "/v4/records/{id}/parcels",         "parcels",        True, None),
    ("GET",  "/v4/records/{id}/contacts",        "contacts",       True, None),
    ("GET",  "/v4/records/{id}/professionals",   "professionals",  True, None),
    ("GET",  "/v4/records/{id}/owners",          "owners",         True, None),
    ("GET",  "/v4/records/{id}/inspections",     "inspections",    True, None),
    ("GET",  "/v4/records/{id}/fees",            "fees",           True, None),
    ("GET",  "/v4/records/{id}/documents",       "documents",      True, None),
    ("GET",  "/v4/records/{id}/workflowTasks",   "workflow-tasks", True, None),
    ("GET",  "/v4/records/{id}/related",         "related",        True, None),
    ("GET",  "/v4/records/{id}/customForms",     "custom-forms",   True, None),
    # Admin/settings (typically requires App Creds)
    ("GET",  "/v4/settings/records/types",       "record-types",       False, None),
    ("GET",  "/v4/settings/inspections/types",   "inspection-types",   False, None),
]


@dataclass
class ProbeResult:
    endpoint: str
    method: str
    path: str
    auth: str  # "anonymous" | "app-creds"
    status: int | None
    note: str
    sample: str = ""
    body: dict | list | None = field(default=None, repr=False)


def search_body(permit_number: str) -> dict:
    """Build a POST /v4/search/records body that filters by altId (human permit #)."""
    return {
        "filters": {
            "record": {
                "altId": permit_number,
            },
        },
    }


def get_app_token(app_id: str, app_secret: str, agency: str, environment: str = "PROD") -> tuple[int, dict | str]:
    """Exchange client credentials for a bearer token scoped to an agency.

    Accela Agency Apps require `agency_name` and `environment` in the token
    request; Citizen Apps may have different requirements. We try the
    Agency-App shape first since our initial probe error indicated that's
    what the app is provisioned as.

    Returns (status_code, parsed_json_or_text).
    """
    resp = requests.post(
        f"{API_BASE}/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": app_id,
            "client_secret": app_secret,
            "agency_name": agency,
            "environment": environment,
            "scope": "records",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    try:
        return resp.status_code, resp.json()
    except ValueError:
        return resp.status_code, resp.text[:500]


def call_endpoint(
    method: str,
    path: str,
    agency: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    environment: str = "PROD",
) -> requests.Response:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "x-accela-agency": agency,
        "x-accela-environment": environment,
        "x-accela-appid": APP_ID,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{API_BASE}{path}"
    kwargs: dict[str, Any] = {"headers": headers, "timeout": REQUEST_TIMEOUT}
    if body is not None:
        kwargs["json"] = body
    return requests.request(method, url, **kwargs)


def summarize_body(resp: requests.Response, max_len: int = 300) -> tuple[str, dict | list | None]:
    """Return (one-line summary, parsed body-if-json)."""
    try:
        parsed = resp.json()
    except ValueError:
        return f"non-JSON body, {len(resp.text)} bytes: {resp.text[:max_len]}", None

    # Accela envelopes: sometimes {"result": [...], "status": 200} sometimes raw list
    if isinstance(parsed, dict):
        if "result" in parsed and isinstance(parsed["result"], list):
            items = parsed["result"]
            return f"{len(items)} result item(s); keys: {sorted(set(k for it in items[:3] if isinstance(it, dict) for k in it.keys()))[:8]}", parsed
        if "error" in parsed or "message" in parsed or "code" in parsed:
            msg = parsed.get("message") or parsed.get("error_description") or parsed.get("error") or ""
            code = parsed.get("code", "")
            return f"error: {code} {msg}"[:max_len], parsed
        return f"dict with keys {sorted(parsed.keys())[:8]}", parsed
    if isinstance(parsed, list):
        keys = sorted(set(k for it in parsed[:3] if isinstance(it, dict) for k in it.keys()))[:8]
        return f"{len(parsed)} item(s); keys: {keys}", parsed
    return f"scalar: {str(parsed)[:max_len]}", parsed


def extract_record_id(search_body_parsed: dict | list | None) -> str | None:
    """Pull the internal record ID from a search response."""
    if search_body_parsed is None:
        return None
    items = search_body_parsed.get("result") if isinstance(search_body_parsed, dict) else search_body_parsed
    if not isinstance(items, list) or not items:
        return None
    first = items[0]
    if not isinstance(first, dict):
        return None
    # Accela typically uses "id" (string, e.g. "POLKCO-26CAP-02894") as the internal record ID
    return first.get("id") or first.get("recordId") or first.get("customId")


def probe(agency: str, permit_number: str) -> list[ProbeResult]:
    results: list[ProbeResult] = []

    # Phase 1: OAuth2 token
    token: str | None = None
    if APP_SECRET:
        status, body = get_app_token(APP_ID, APP_SECRET, agency)
        if status == 200 and isinstance(body, dict):
            token = body.get("access_token")
            sample = f"token acquired, expires_in={body.get('expires_in')}"
        else:
            sample = f"token request failed: {body if isinstance(body, str) else json.dumps(body)[:300]}"
        results.append(ProbeResult(
            endpoint="oauth2-token",
            method="POST",
            path="/oauth2/token",
            auth="client_credentials",
            status=status,
            note="App Creds token exchange",
            sample=sample,
        ))
    else:
        results.append(ProbeResult(
            endpoint="oauth2-token",
            method="POST",
            path="/oauth2/token",
            auth="client_credentials",
            status=None,
            note="skipped — ACCELA_APP_SECRET not set",
        ))

    # Phase 2: Search to discover internal record ID
    internal_record_id: str | None = None
    for auth_label, auth_token in [("anonymous", None), ("app-creds", token)]:
        if auth_label == "app-creds" and not auth_token:
            continue
        try:
            resp = call_endpoint(
                "POST", "/v4/search/records", agency,
                token=auth_token, body=search_body(permit_number),
            )
            sample, parsed = summarize_body(resp)
            if internal_record_id is None:
                internal_record_id = extract_record_id(parsed)
        except requests.RequestException as e:
            sample, parsed = f"network error: {e}", None
            resp = None
        results.append(ProbeResult(
            endpoint="search-records",
            method="POST",
            path="/v4/search/records",
            auth=auth_label,
            status=resp.status_code if resp else None,
            note=f"altId={permit_number}",
            sample=sample,
            body=parsed,
        ))

    # Phase 3: Per-endpoint probe with whatever record ID we have (human permit as fallback)
    record_id_to_use = internal_record_id or permit_number

    for method, path_template, label, requires_id, body_key in ENDPOINTS:
        if label == "search-records":
            continue  # already probed in phase 2
        path = path_template.replace("{id}", record_id_to_use) if requires_id else path_template

        for auth_label, auth_token in [("anonymous", None), ("app-creds", token)]:
            if auth_label == "app-creds" and not auth_token:
                continue
            try:
                resp = call_endpoint(method, path, agency, token=auth_token)
                sample, parsed = summarize_body(resp)
                status = resp.status_code
            except requests.RequestException as e:
                sample, parsed = f"network error: {e}", None
                status = None
            note = f"record_id={record_id_to_use}" if requires_id else ""
            results.append(ProbeResult(
                endpoint=label,
                method=method,
                path=path,
                auth=auth_label,
                status=status,
                note=note,
                sample=sample,
                body=parsed,
            ))

    return results


def format_report(
    agency: str,
    permit_number: str,
    results: list[ProbeResult],
) -> str:
    lines = []
    lines.append(f"# Accela v4 REST Probe — {agency}")
    lines.append(f"")
    lines.append(f"Run: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Agency: `{agency}`")
    lines.append(f"Probe record (altId): `{permit_number}`")
    lines.append(f"App ID: `{APP_ID[:4]}...{APP_ID[-4:]}`  (full value in .env)")
    lines.append(f"App Secret present: {'yes' if APP_SECRET else 'no'}")
    lines.append(f"")
    lines.append(f"## Compatibility matrix")
    lines.append(f"")
    lines.append(f"| Endpoint | Method | Auth | Status | Summary |")
    lines.append(f"|---|---|---|---|---|")
    for r in results:
        status = str(r.status) if r.status is not None else "--"
        sample = (r.sample or r.note or "").replace("|", "\\|").replace("\n", " ")
        if len(sample) > 120:
            sample = sample[:117] + "..."
        lines.append(f"| `{r.endpoint}` | `{r.method}` | {r.auth} | {status} | {sample} |")
    lines.append(f"")
    lines.append(f"## Verdict")
    lines.append(f"")

    ok_count = sum(1 for r in results if r.status == 200)
    auth_fail_count = sum(1 for r in results if r.status in (401, 403))
    not_found_count = sum(1 for r in results if r.status == 404)
    total_probes = len(results)

    lines.append(f"- Probes total: {total_probes}")
    lines.append(f"- 200 OK: {ok_count}")
    lines.append(f"- 401/403 auth/permission: {auth_fail_count}")
    lines.append(f"- 404 not found: {not_found_count}")

    # Classify the run
    token_row = next((r for r in results if r.endpoint == "oauth2-token"), None)
    search_anon = next((r for r in results if r.endpoint == "search-records" and r.auth == "anonymous"), None)
    search_creds = next((r for r in results if r.endpoint == "search-records" and r.auth == "app-creds"), None)

    lines.append(f"")
    lines.append(f"**Signals:**")
    if token_row and token_row.status == 200:
        lines.append(f"- OAuth2 client_credentials: ✅ accepted — app is correctly provisioned for App Creds flow")
    elif token_row and token_row.status is not None:
        lines.append(f"- OAuth2 client_credentials: ❌ {token_row.status} — app may be wrong type (Agency vs Citizen) or scope issue")
    if search_anon and search_anon.status == 200:
        lines.append(f"- Anonymous search: ✅ working — agency has anonymous access enabled")
    elif search_anon and search_anon.status in (401, 403):
        lines.append(f"- Anonymous search: ❌ {search_anon.status} — agency requires auth for search")
    if search_creds and search_creds.status == 200:
        lines.append(f"- App-creds search: ✅ working")

    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--agency", default="POLKCO", help="Accela agency code")
    p.add_argument("--permit", default="BR-2026-2894", help="Known human permit number (altId)")
    p.add_argument("--out", default=None, help="Optional output markdown file; defaults to stdout")
    args = p.parse_args()

    results = probe(args.agency, args.permit)
    report = format_report(args.agency, args.permit, results)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"Wrote {args.out} ({len(report)} bytes)", file=sys.stderr)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
