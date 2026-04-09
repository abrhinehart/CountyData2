"""
cookie_session.py - Selenium cookie capture for captcha-hybrid county portals.

Opens a real browser so the user can solve a CAPTCHA / accept a disclaimer,
then harvests cookies and applies them to a plain requests.Session.
"""

import requests


def capture_cookies(url: str, *, prompt: str | None = None) -> dict[str, str]:
    """Open a Chrome window, wait for the user to complete manual steps, return cookies.

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

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd(
        'Page.addScriptToEvaluateOnNewDocument',
        {'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
    )

    driver.get(url)

    msg = prompt or f'\n  Browser opened to {url}.\n  Complete any manual steps, then press Enter here to continue.\n'
    print(msg)
    input('  Press Enter when ready...')

    cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    driver.quit()
    return cookies


def apply_cookies_to_session(session: requests.Session, cookies: dict[str, str]) -> None:
    """Copy a dict of cookies into an existing requests.Session."""
    for name, value in cookies.items():
        session.cookies.set(name, value)
