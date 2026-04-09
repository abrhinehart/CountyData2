"""Tests for cookie_session utilities and LandmarkSession.from_cookies."""

import unittest

import requests

from county_scrapers.cookie_session import apply_cookies_to_session
from county_scrapers.landmark_client import LandmarkSession


class ApplyCookiesTests(unittest.TestCase):
    def test_cookies_set_on_session(self):
        session = requests.Session()
        apply_cookies_to_session(session, {'session_id': 'abc123', 'token': 'xyz789'})
        self.assertEqual(session.cookies.get('session_id'), 'abc123')
        self.assertEqual(session.cookies.get('token'), 'xyz789')

    def test_empty_cookies(self):
        session = requests.Session()
        apply_cookies_to_session(session, {})
        self.assertEqual(len(session.cookies), 0)


class FromCookiesTests(unittest.TestCase):
    def test_creates_connected_session(self):
        session = LandmarkSession.from_cookies(
            'https://example.com', {'k': 'v'})
        self.assertTrue(session._connected)

    def test_cookies_present(self):
        session = LandmarkSession.from_cookies(
            'https://example.com', {'session_id': 'test123'})
        self.assertEqual(session._session.cookies.get('session_id'), 'test123')

    def test_base_url_set(self):
        session = LandmarkSession.from_cookies(
            'https://example.com/Recording', {'k': 'v'})
        self.assertEqual(session.base_url, 'https://example.com/Recording')


if __name__ == '__main__':
    unittest.main()
