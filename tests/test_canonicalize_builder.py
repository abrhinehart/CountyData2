import unittest

from modules.permits.normalization import canonicalize_builder_name


class CanonicalizeBuilderNameTests(unittest.TestCase):
    def test_none_returns_unknown(self):
        self.assertEqual(canonicalize_builder_name(None), "Unknown Builder")

    def test_empty_string_returns_unknown(self):
        self.assertEqual(canonicalize_builder_name(""), "Unknown Builder")

    def test_whitespace_only_returns_unknown(self):
        self.assertEqual(canonicalize_builder_name("   "), "Unknown Builder")

    def test_known_builder_returns_canonical(self):
        result = canonicalize_builder_name("DR Horton Inc")
        self.assertEqual(result, "DR Horton")


if __name__ == "__main__":
    unittest.main()
