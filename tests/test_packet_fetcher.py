"""Unit tests for modules.commission.packet_fetcher helpers.

Regression coverage for Entry 11 of docs/unification/post-merge-quirks.md:
`_parse_desc_fields` must handle both the legacy span-wrapped CivicPlus
shape AND the bare-text-after-strong shape seen in the Mar 9 Panama City
Planning Board agenda (`source_doc.id=8`, cases CPC-PLN-2026-0626 and
CPC-PLN-2026-0633).
"""

import unittest

from bs4 import BeautifulSoup

from modules.commission.packet_fetcher import _parse_desc_fields


def _desc(html):
    """Wrap a <div class='desc'> around the given inner HTML and return
    the BeautifulSoup Tag for the div."""
    return BeautifulSoup(f'<div class="desc">{html}</div>', "html.parser").div


class ParseDescFieldsSpanWrappedTests(unittest.TestCase):
    """Happy path — legacy span-wrapped shape (Feb 9 agenda, id=9)."""

    def test_parses_span_wrapped_label_value_pairs(self):
        html = (
            '<p><strong><span>Application Type:</span></strong>'
            '<span>Rezoning</span></p>'
            '<p><strong><span>Owner:</span></strong>'
            '<span>Jane Doe</span></p>'
            '<p><strong><span>Applicant:</span></strong>'
            '<span>ACME LLC</span></p>'
        )
        result = _parse_desc_fields(_desc(html))
        self.assertEqual(result["application type"], "Rezoning")
        self.assertEqual(result["owner"], "Jane Doe")
        self.assertEqual(result["applicant"], "ACME LLC")
        self.assertEqual(len(result), 3)


class ParseDescFieldsBareTextTests(unittest.TestCase):
    """Entry 11 drift — bare NavigableString after </strong>.

    HTML samples lifted verbatim from Panama City Planning Board
    Agenda_03092026-847.pdf (source_doc.id=8), the exact content that
    caused `_parse_desc_fields` to silently return {}.
    """

    def test_colon_after_strong_no_nbsp(self):
        html = (
            '<p data-pasted="true"><strong>Application Type</strong>'
            ': Conceptual Plan</p>'
        )
        result = _parse_desc_fields(_desc(html))
        self.assertEqual(result, {"application type": "Conceptual Plan"})

    def test_colon_inside_strong_with_nbsp(self):
        html = (
            '<p><strong>Owner:&nbsp;</strong>'
            'SWEETBAY TOWNCENTER PH 1, LLC</p>'
        )
        result = _parse_desc_fields(_desc(html))
        self.assertEqual(result, {"owner": "SWEETBAY TOWNCENTER PH 1, LLC"})

    def test_mar_9_full_agenda_shape(self):
        """All three Mar 9 paragraphs in a single desc div — the exact
        live drift case. Pre-fix this returned {} (0 keys); post-fix must
        return 3 keys."""
        html = (
            '<p data-pasted="true"><strong>Application Type</strong>'
            ': Conceptual Plan</p>'
            '<p><strong>Owner:&nbsp;</strong>'
            'SWEETBAY TOWNCENTER PH 1, LLC</p>'
            '<p><strong>Applicant:&nbsp;</strong>'
            'Richard Pfuntner, Dewberry Engineers, Inc.</p>'
        )
        result = _parse_desc_fields(_desc(html))
        self.assertEqual(result["application type"], "Conceptual Plan")
        self.assertEqual(result["owner"], "SWEETBAY TOWNCENTER PH 1, LLC")
        self.assertEqual(
            result["applicant"],
            "Richard Pfuntner, Dewberry Engineers, Inc.",
        )
        self.assertEqual(len(result), 3)


class ParseDescFieldsMixedShapeTests(unittest.TestCase):
    """Guard for the hypothetical case where a single desc div contains
    paragraphs in BOTH shapes. This shouldn't happen in the wild (a
    single agenda item tends to be authored in one style) but the
    parser must not regress on either shape when they are interleaved.
    """

    def test_mixed_span_wrapped_and_bare_text(self):
        html = (
            '<p><strong><span>Application Type:</span></strong>'
            '<span>Rezoning</span></p>'
            '<p><strong>Owner:&nbsp;</strong>Jane Doe</p>'
        )
        result = _parse_desc_fields(_desc(html))
        self.assertEqual(result["application type"], "Rezoning")
        self.assertEqual(result["owner"], "Jane Doe")
        self.assertEqual(len(result), 2)


class ParseDescFieldsEdgeCaseTests(unittest.TestCase):
    """Edge cases — empty desc, strong without value, non-strong paragraphs."""

    def test_empty_desc_returns_empty_dict(self):
        self.assertEqual(_parse_desc_fields(_desc("")), {})

    def test_paragraphs_without_strong_are_skipped(self):
        html = "<p>Just a plain sentence.</p><p>Another one.</p>"
        self.assertEqual(_parse_desc_fields(_desc(html)), {})

    def test_strong_with_no_value_is_skipped(self):
        html = "<p><strong>Label:</strong></p>"
        self.assertEqual(_parse_desc_fields(_desc(html)), {})

    def test_strong_with_only_whitespace_after_is_skipped(self):
        html = "<p><strong>Label:</strong>   </p>"
        self.assertEqual(_parse_desc_fields(_desc(html)), {})


if __name__ == "__main__":
    unittest.main()
