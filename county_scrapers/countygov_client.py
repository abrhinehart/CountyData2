"""
countygov_client.py - HTTP client for CountyGovServices portals (Azure AD B2C auth).

Handles B2C authentication, session management, searching by date range,
and parsing Kendo Grid JSON responses. No Selenium.

Usage:
    from county_scrapers.countygov_client import CountyGovSession

    session = CountyGovSession(
        "https://madisonprobate.countygovservices.com",
        email="user@example.com",
        password="secret",
    )
    session.connect()
    rows = session.search_by_date_range("01/01/2025", "01/31/2025")
"""

import logging
import re
import time
from urllib.parse import parse_qs, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r'<[^>]+>')
_BR_RE = re.compile(r'<br\s*/?>', re.IGNORECASE)


class AuthenticationError(Exception):
    """Raised when B2C authentication fails."""


def _clean_name(value: str) -> str:
    """Replace <br/> and <br> with '; ', strip remaining HTML tags, normalize whitespace."""
    if not value:
        return ''
    text = _BR_RE.sub('; ', value)
    text = _HTML_TAG_RE.sub('', text)
    text = re.sub(r'\s+', ' ', text).strip()
    # Strip leading/trailing semicolons left by empty segments
    text = text.strip('; ').strip()
    return text


def _convert_date(iso_date: str) -> str:
    """Convert ISO-ish date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) to MM/DD/YYYY."""
    if not iso_date:
        return ''
    # Take just the date portion
    date_part = iso_date[:10]
    parts = date_part.split('-')
    if len(parts) == 3:
        return f'{parts[1]}/{parts[2]}/{parts[0]}'
    return iso_date


class CountyGovSession:
    """Stateful HTTP client for a single CountyGovServices portal."""

    def __init__(self, base_url: str, email: str, password: str,
                 b2c_tenant: str | None = None, b2c_policy: str | None = None,
                 search_type: str = 'deed', page_size: int = 500,
                 request_delay: float = 1.0):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self.b2c_tenant = b2c_tenant
        self.b2c_policy = b2c_policy
        self.search_type = search_type
        self.page_size = page_size
        self.request_delay = request_delay

        self._session = requests.Session()
        retry = Retry(total=3, backoff_factor=1.5,
                      status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount('https://', adapter)
        self._session.mount('http://', adapter)
        self._session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
        })
        self._connected = False
        self._verification_token = ''

    def connect(self) -> None:
        """Authenticate via Azure AD B2C and establish session."""
        log.info('Connecting to %s', self.base_url)

        # Step 1: GET base_url with no redirects to capture B2C authorize URL
        resp = self._session.get(f'{self.base_url}/', allow_redirects=False, timeout=30)
        if resp.status_code not in (301, 302, 303, 307):
            raise AuthenticationError(
                f'Expected redirect from {self.base_url}/, got {resp.status_code}')

        authorize_url = resp.headers.get('Location', '')
        log.debug('B2C authorize URL: %s', authorize_url)

        parsed = urlparse(authorize_url)
        params = parse_qs(parsed.query)

        # Extract or use provided tenant/policy
        if self.b2c_tenant:
            tenant = self.b2c_tenant
        else:
            # Tenant is the hostname prefix, e.g., "tenantname.b2clogin.com"
            tenant = parsed.hostname or ''

        client_id = params.get('client_id', [''])[0]
        redirect_uri = params.get('redirect_uri', [''])[0]

        # Step 2: GET the B2C authorize URL and parse SETTINGS
        resp = self._session.get(authorize_url, timeout=30)
        resp.raise_for_status()

        csrf_match = re.search(r'"csrf"\s*:\s*"([^"]+)"', resp.text)
        trans_match = re.search(r'"transId"\s*:\s*"([^"]+)"', resp.text)

        if not csrf_match:
            raise AuthenticationError('Could not find SETTINGS.csrf in B2C page')
        if not trans_match:
            raise AuthenticationError('Could not find SETTINGS.transId in B2C page')

        csrf = csrf_match.group(1)
        trans_id = trans_match.group(1)
        log.debug('B2C csrf=%s, transId=%s', csrf, trans_id)

        # Extract policy: query param 'p', SETTINGS hosts.policy, or path segment
        if self.b2c_policy:
            policy = self.b2c_policy
        else:
            policy = params.get('p', [''])[0]
            if not policy:
                # Try SETTINGS hosts.policy (correct casing)
                policy_match = re.search(
                    r'"hosts"\s*:.*?"policy"\s*:\s*"([^"]+)"', resp.text)
                if policy_match:
                    policy = policy_match.group(1)
            if not policy:
                # Fallback: extract from path segments
                for seg in parsed.path.split('/'):
                    if seg.lower().startswith('b2c_'):
                        policy = seg
                        break

        if not policy:
            raise AuthenticationError('Could not extract B2C policy from redirect URL')

        # Step 3: Build b2c_base and POST credentials
        # b2c_base = scheme + host + path up through the policy segment.
        # Prefer hosts.tenant from SETTINGS (correct casing) over path parsing.
        hosts_tenant_match = re.search(
            r'"hosts"\s*:.*?"tenant"\s*:\s*"([^"]+)"', resp.text)
        if hosts_tenant_match:
            b2c_base = f'{parsed.scheme}://{parsed.hostname}{hosts_tenant_match.group(1)}'
        else:
            policy_lower = policy.lower()
            segments = [s for s in parsed.path.split('/') if s]
            b2c_segments = []
            for seg in segments:
                b2c_segments.append(seg)
                if seg.lower() == policy_lower:
                    break
            b2c_base = f'{parsed.scheme}://{parsed.hostname}/{"/".join(b2c_segments)}'

        # Some B2C tenants use /api/ prefixed endpoints, others don't.
        # Each endpoint may independently require or reject the prefix,
        # so we probe each one separately.
        _cred_data = {
            'request_type': 'RESPONSE',
            'email': self.email,
            'password': self.password,
        }
        _cred_headers = {
            'X-CSRF-TOKEN': csrf,
            'X-Requested-With': 'XMLHttpRequest',
        }

        for prefix in ('api/', ''):
            self_asserted_url = (
                f'{b2c_base}/{prefix}SelfAsserted?tx={trans_id}&p={policy}'
            )
            resp = self._session.post(
                self_asserted_url,
                data=_cred_data,
                headers=_cred_headers,
                timeout=30,
            )
            if resp.status_code == 404:
                log.debug('SelfAsserted 404 with prefix=%r, trying next', prefix)
                continue
            resp.raise_for_status()
            break
        else:
            raise AuthenticationError(
                'B2C SelfAsserted returned 404 for both /api/ and root paths')

        resp_data = resp.json()
        if str(resp_data.get('status')) != '200':
            raise AuthenticationError(
                f'B2C SelfAsserted returned status {resp_data.get("status")}: '
                f'{resp_data.get("message", "unknown error")}')

        # Step 4: GET confirmed endpoint to get code and state
        for prefix in ('api/', ''):
            confirmed_url = (
                f'{b2c_base}/{prefix}CombinedSigninAndSignup/confirmed'
                f'?rememberMe=false&csrf_token={csrf}&tx={trans_id}&p={policy}'
            )
            resp = self._session.get(confirmed_url, timeout=30)
            if resp.status_code == 404:
                log.debug('confirmed 404 with prefix=%r, trying next', prefix)
                continue
            resp.raise_for_status()
            break
        else:
            raise AuthenticationError(
                'B2C confirmed returned 404 for both /api/ and root paths')

        code_match = re.search(
            r'<input[^>]+name=["\']code["\'][^>]+value=["\']([^"\']+)["\']', resp.text)
        state_match = re.search(
            r'<input[^>]+name=["\']state["\'][^>]+value=["\']([^"\']+)["\']', resp.text)

        if not code_match:
            # Try alternate attribute order: value before name
            code_match = re.search(
                r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']code["\']', resp.text)
        if not state_match:
            state_match = re.search(
                r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']state["\']', resp.text)

        if not code_match or not state_match:
            raise AuthenticationError('Could not find code/state in B2C confirmed response')

        code = code_match.group(1)
        state = state_match.group(1)

        # Step 5: POST code/state to redirect_uri to set session cookie
        resp = self._session.post(
            redirect_uri,
            data={'code': code, 'state': state},
            timeout=30,
        )
        resp.raise_for_status()
        log.info('B2C authentication complete, session cookie set')

        # Step 6: GET Requirements page and extract verification token
        resp = self._session.get(f'{self.base_url}/Home/Requirements', timeout=30)
        resp.raise_for_status()

        token_match = re.search(
            r'<input[^>]+name=["\']__RequestVerificationToken["\'][^>]+'
            r'value=["\']([^"\']+)["\']',
            resp.text,
        )
        if not token_match:
            token_match = re.search(
                r'<input[^>]+value=["\']([^"\']+)["\'][^>]+'
                r'name=["\']__RequestVerificationToken["\']',
                resp.text,
            )

        verification_token = token_match.group(1) if token_match else ''

        # Step 7: POST to accept terms
        resp = self._session.post(
            f'{self.base_url}/Home/Requirements',
            data={
                'TermsAccepted': 'true',
                '__RequestVerificationToken': verification_token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        log.info('Terms accepted')

        self._connected = True

    def search_by_date_range(self, begin_date: str, end_date: str) -> list[dict]:
        """
        Search by recording date range.

        Args:
            begin_date: MM/DD/YYYY
            end_date: MM/DD/YYYY

        Returns list of parsed record dicts.
        """
        self._ensure_connected()
        log.info('Searching records %s to %s (search_type=%s)',
                 begin_date, end_date, self.search_type)

        # Step 1: GET SearchType page to get SearchQueryId
        resp = self._session.get(
            f'{self.base_url}/Search/SearchType',
            params={'key': self.search_type},
            timeout=30,
        )
        resp.raise_for_status()

        sqid_match = re.search(r'data-searchqueryid=["\']([^"\']+)["\']', resp.text)
        if not sqid_match:
            sqid_match = re.search(
                r'<input[^>]+name=["\']SearchQueryId["\'][^>]+value=["\']([^"\']+)["\']',
                resp.text,
            )
        search_query_id = sqid_match.group(1) if sqid_match else ''
        log.debug('SearchQueryId: %s', search_query_id)

        # Step 2: GET SearchResults with params
        search_params = {
            'SearchQueryId': search_query_id,
            'SearchType': self.search_type,
            'StartDate': begin_date,
            'EndDate': end_date,
            'InstrumentTypeID': '0',
            'AllNamesOne': '',
            'AllNamesTwo': '',
            'Description': '',
            'BookNumber': '',
            'DocNumber': '',
            'ShowIndividuals': 'false',
            'AllNameOneDirectionID': '0',
            'AllNameTwoDirectionID': '0',
            'AllNameOneMatchType': 'begins',
            'AllNameTwoMatchType': 'begins',
        }
        resp = self._session.get(
            f'{self.base_url}/Search/SearchResults',
            params=search_params,
            timeout=60,
        )
        resp.raise_for_status()

        # Step 3: Parse Kendo Grid config for query and qid
        query_match = re.search(r'["\']?query["\']?\s*:\s*["\']([^"\']+)["\']', resp.text)
        qid_match = re.search(
            r'(?:data-searchqueryid|["\']?qid["\']?)\s*[:=]\s*["\']([^"\']+)["\']',
            resp.text,
        )

        query = query_match.group(1) if query_match else ''
        qid = qid_match.group(1) if qid_match else search_query_id
        log.debug('Kendo grid query=%s, qid=%s', query, qid)

        time.sleep(self.request_delay)

        # Step 4: Paginate through SearchResultsGrid
        all_rows = []
        page = 1

        while True:
            resp = self._session.post(
                f'{self.base_url}/Search/SearchResultsGrid',
                data={
                    'sort': '',
                    'page': str(page),
                    'pageSize': str(self.page_size),
                    'group': '',
                    'filter': '',
                    'query': query,
                    'qid': qid,
                },
                headers={'X-Requested-With': 'XMLHttpRequest'},
                timeout=60,
            )
            resp.raise_for_status()

            data = resp.json()
            total = int(data.get('Total', 0))
            page_data = data.get('Data', [])

            if not page_data:
                break

            for raw in page_data:
                parsed = self._parse_row(raw)
                if parsed:
                    all_rows.append(parsed)

            log.info('  fetched %d/%d records', len(all_rows), total)

            if len(all_rows) >= total:
                break

            page += 1
            time.sleep(self.request_delay)

        log.info('Total records retrieved: %d', len(all_rows))
        return all_rows

    def _parse_row(self, raw: dict) -> dict | None:
        """Parse a single Kendo Grid row dict into a clean record."""
        parsed = {
            'instrument': str(raw.get('iID', '')),
            'grantor': _clean_name(str(raw.get('Name1', ''))),
            'grantee': _clean_name(str(raw.get('Name2', ''))),
            'doc_type': str(raw.get('itNAME', '')),
            'record_date': _convert_date(str(raw.get('iRECORDED', ''))),
            'legal': str(raw.get('iDESC', '')),
            'book': str(raw.get('bkNAME', '')),
            'page': str(raw.get('iNUMBER', '')),
            'book_type': str(raw.get('bktNAME', '')),
            'page_count': str(raw.get('iPAGES', '')),
            'instrument_type_id': str(raw.get('itID', '')),
            'mortgage_value': str(raw.get('idVALUE_MORT', '')),
            'subdivision_value': str(raw.get('idVALUE_SUBDIV', '')),
        }
        # Filter zero mortgage values
        if parsed['mortgage_value'] in ('0', '0.0', '0.00', ''):
            parsed['mortgage_value'] = ''
        return parsed if any(v for k, v in parsed.items()) else None

    def _ensure_connected(self) -> None:
        if not self._connected:
            self.connect()

    def close(self) -> None:
        self._session.close()
        self._connected = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
