"""
cookie_session.py - Selenium cookie capture for captcha-hybrid and Cloudflare county portals.

Opens a real browser so the user can solve a CAPTCHA / accept a disclaimer,
then harvests cookies and applies them to a plain requests.Session.
"""

import logging
import time

import requests

log = logging.getLogger(__name__)


def _build_driver(*, headless: bool = False):
    """Create a Chrome WebDriver with anti-detection options.

    Selenium is imported inside this function so the module can be imported
    without requiring Selenium at the top level.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=1600,1200')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    if headless:
        options.add_argument('--headless=new')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd(
        'Page.addScriptToEvaluateOnNewDocument',
        {'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
    )
    return driver


def capture_cookies(url: str, *, prompt: str | None = None) -> dict[str, str]:
    """Open a Chrome window, wait for the user to complete manual steps, return cookies."""
    driver = _build_driver(headless=False)
    driver.get(url)

    msg = prompt or f'\n  Browser opened to {url}.\n  Complete any manual steps, then press Enter here to continue.\n'
    print(msg)
    input('  Press Enter when ready...')

    cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    driver.quit()
    return cookies


def capture_cloudflare_cookies(url: str, *, timeout: int = 60) -> dict[str, str]:
    """Solve a Cloudflare challenge and accept the LandmarkWeb disclaimer, returning cookies.

    Tries headless Chrome first; if the cf_clearance cookie is not obtained
    within half the timeout, falls back to a visible browser for the remaining time.
    After Cloudflare clears, POSTs to the LandmarkWeb SetDisclaimer endpoint so
    the returned cookies are ready for API use.
    """

    def _poll_for_clearance(driver, seconds: int) -> bool:
        """Poll driver cookies for cf_clearance. Returns True if found."""
        elapsed = 0
        while elapsed < seconds:
            names = {c['name'] for c in driver.get_cookies()}
            if 'cf_clearance' in names:
                return True
            time.sleep(2)
            elapsed += 2
        return False

    def _accept_disclaimer(driver, url: str) -> None:
        """POST the LandmarkWeb SetDisclaimer endpoint via the browser JS context."""
        base = url.rsplit('/Home', 1)[0] if '/Home' in url else url.rstrip('/')
        driver.get(base + '/Home/Index')
        time.sleep(2)
        driver.execute_script(
            "fetch('" + base + "/Search/SetDisclaimer', "
            "{method: 'POST', headers: {'X-Requested-With': 'XMLHttpRequest'}})"
        )
        time.sleep(1)

    half = timeout // 2

    # --- Attempt 1: headless ---
    log.info('Attempting Cloudflare challenge in headless mode (%ds)...', half)
    driver = _build_driver(headless=True)
    try:
        driver.get(url)
        if _poll_for_clearance(driver, half):
            log.info('Cloudflare cleared in headless mode.')
            _accept_disclaimer(driver, url)
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            return cookies
    finally:
        driver.quit()

    # --- Attempt 2: visible browser ---
    remaining = timeout - half
    log.warning('Headless failed; retrying with visible Chrome (%ds)...', remaining)
    driver = _build_driver(headless=False)
    try:
        driver.get(url)
        if _poll_for_clearance(driver, remaining):
            log.info('Cloudflare cleared in visible mode.')
            _accept_disclaimer(driver, url)
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            return cookies
    finally:
        driver.quit()

    raise RuntimeError('Cloudflare challenge not solved within timeout')


def apply_cookies_to_session(session: requests.Session, cookies: dict[str, str]) -> None:
    """Copy a dict of cookies into an existing requests.Session."""
    for name, value in cookies.items():
        session.cookies.set(name, value)
