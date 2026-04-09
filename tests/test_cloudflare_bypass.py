"""Tests for Cloudflare bypass cookie capture and Escambia config."""

import unittest
from unittest.mock import MagicMock, patch, call

from county_scrapers.configs import list_working_counties
from county_scrapers.landmark_client import LandmarkSession


class CloudflareBypassTests(unittest.TestCase):

    @patch('county_scrapers.cookie_session._build_driver')
    def test_success_headless(self, mock_build):
        """cf_clearance found on first headless poll => returns cookies, no visible fallback."""
        mock_driver = MagicMock()
        mock_build.return_value = mock_driver
        mock_driver.get_cookies.return_value = [
            {'name': 'cf_clearance', 'value': 'abc123'},
            {'name': '__cf_bm', 'value': 'xyz789'},
        ]

        from county_scrapers.cookie_session import capture_cloudflare_cookies
        cookies = capture_cloudflare_cookies(
            'https://dory.escambiaclerk.com/LandmarkWeb/Home/Index', timeout=10)

        self.assertEqual(cookies['cf_clearance'], 'abc123')
        self.assertEqual(cookies['__cf_bm'], 'xyz789')
        # Only one driver built (headless) since it succeeded immediately
        mock_build.assert_called_once_with(headless=True)
        mock_driver.quit.assert_called_once()

    @patch('county_scrapers.cookie_session._build_driver')
    @patch('county_scrapers.cookie_session.time')
    def test_headless_fallback_to_visible(self, mock_time, mock_build):
        """Headless never gets cf_clearance; visible Chrome succeeds."""
        headless_driver = MagicMock(name='headless')
        visible_driver = MagicMock(name='visible')
        mock_build.side_effect = [headless_driver, visible_driver]

        # Headless always returns no cf_clearance
        headless_driver.get_cookies.return_value = [
            {'name': '__cf_bm', 'value': 'bm_only'},
        ]
        # Visible returns cf_clearance on first poll
        visible_driver.get_cookies.return_value = [
            {'name': 'cf_clearance', 'value': 'vis_clear'},
            {'name': '__cf_bm', 'value': 'vis_bm'},
        ]

        from county_scrapers.cookie_session import capture_cloudflare_cookies
        cookies = capture_cloudflare_cookies(
            'https://dory.escambiaclerk.com/LandmarkWeb/Home/Index', timeout=10)

        self.assertEqual(cookies['cf_clearance'], 'vis_clear')
        # Two drivers built: headless then visible
        self.assertEqual(mock_build.call_count, 2)
        mock_build.assert_any_call(headless=True)
        mock_build.assert_any_call(headless=False)
        headless_driver.quit.assert_called_once()
        visible_driver.quit.assert_called_once()

    @patch('county_scrapers.cookie_session._build_driver')
    @patch('county_scrapers.cookie_session.time')
    def test_total_failure_raises(self, mock_time, mock_build):
        """Neither headless nor visible obtains cf_clearance => RuntimeError."""
        driver = MagicMock()
        mock_build.return_value = driver
        driver.get_cookies.return_value = [
            {'name': '__cf_bm', 'value': 'irrelevant'},
        ]

        from county_scrapers.cookie_session import capture_cloudflare_cookies
        with self.assertRaises(RuntimeError) as ctx:
            capture_cloudflare_cookies(
                'https://example.com/LandmarkWeb/Home/Index', timeout=4)
        self.assertIn('Cloudflare challenge not solved', str(ctx.exception))

    @patch('county_scrapers.cookie_session._build_driver')
    def test_disclaimer_posted(self, mock_build):
        """After cf_clearance obtained, SetDisclaimer JS is executed."""
        mock_driver = MagicMock()
        mock_build.return_value = mock_driver
        mock_driver.get_cookies.return_value = [
            {'name': 'cf_clearance', 'value': 'ok'},
        ]

        from county_scrapers.cookie_session import capture_cloudflare_cookies
        capture_cloudflare_cookies(
            'https://dory.escambiaclerk.com/LandmarkWeb/Home/Index', timeout=10)

        # Verify the disclaimer step navigated to /Home/Index and ran JS
        get_calls = [c for c in mock_driver.get.call_args_list]
        urls = [c[0][0] for c in get_calls]
        self.assertTrue(any('/Home/Index' in u for u in urls))
        mock_driver.execute_script.assert_called_once()
        js_arg = mock_driver.execute_script.call_args[0][0]
        self.assertIn('SetDisclaimer', js_arg)


class CffiSessionTests(unittest.TestCase):

    def test_cffi_flag_creates_cffi_session(self):
        session = LandmarkSession('https://example.com', use_cffi=True)
        # curl_cffi session should NOT be an instance of requests.Session
        import requests as std_requests
        self.assertNotIsInstance(session._session, std_requests.Session)
        session.close()


class ConfigTests(unittest.TestCase):

    def test_escambia_in_working_counties(self):
        counties = list_working_counties()
        self.assertIn('Escambia', counties)

    def test_escambia_status_is_cloudflare(self):
        from county_scrapers.configs import LANDMARK_COUNTIES
        self.assertEqual(LANDMARK_COUNTIES['Escambia']['status'], 'cloudflare')


if __name__ == '__main__':
    unittest.main()
