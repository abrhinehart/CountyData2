import unittest
from county_scrapers.pull_records import _extract_last_names, _match_mortgages
from county_scrapers.countygov_client import CountyGovSession


class ExtractLastNamesTests(unittest.TestCase):
    def test_basic(self):
        result = _extract_last_names('SMITH JOHN; DOE JANE')
        self.assertEqual(result, {'SMITH', 'DOE'})

    def test_empty(self):
        result = _extract_last_names('')
        self.assertEqual(result, set())

    def test_single_letter_skipped(self):
        result = _extract_last_names('A SMITH; DOE JANE')
        self.assertEqual(result, {'SMITH', 'DOE'})

    def test_entity_name(self):
        result = _extract_last_names('DHI MORTGAGE CO LTD')
        self.assertEqual(result, {'DHI'})


class MatchMortgagesTests(unittest.TestCase):
    def test_basic_match(self):
        deeds = [{'grantee': 'SMITH JOHN', 'record_date': '03/15/2026'}]
        mortgages = [{'grantor': 'SMITH JOHN', 'grantee': 'DHI MORTGAGE CO LTD',
                      'record_date': '03/15/2026', 'mortgage_value': '280000'}]
        _match_mortgages(deeds, mortgages)
        self.assertEqual(deeds[0]['mortgage_amount'], '280000')
        self.assertEqual(deeds[0]['mortgage_originator'], 'DHI MORTGAGE CO LTD')

    def test_no_match_different_date(self):
        deeds = [{'grantee': 'SMITH JOHN', 'record_date': '03/15/2026'}]
        mortgages = [{'grantor': 'SMITH JOHN', 'grantee': 'BANK',
                      'record_date': '03/16/2026', 'mortgage_value': '280000'}]
        _match_mortgages(deeds, mortgages)
        self.assertNotIn('mortgage_amount', deeds[0])

    def test_no_match_different_name(self):
        deeds = [{'grantee': 'SMITH JOHN', 'record_date': '03/15/2026'}]
        mortgages = [{'grantor': 'JONES BOB', 'grantee': 'BANK',
                      'record_date': '03/15/2026', 'mortgage_value': '280000'}]
        _match_mortgages(deeds, mortgages)
        self.assertNotIn('mortgage_amount', deeds[0])

    def test_multiple_parties(self):
        deeds = [{'grantee': 'SMITH JOHN; SMITH JANE', 'record_date': '03/15/2026'}]
        mortgages = [{'grantor': 'SMITH JOHN', 'grantee': 'BANK',
                      'record_date': '03/15/2026', 'mortgage_value': '300000'}]
        _match_mortgages(deeds, mortgages)
        self.assertEqual(deeds[0]['mortgage_amount'], '300000')

    def test_mortgage_originator(self):
        deeds = [{'grantee': 'DOE JANE', 'record_date': '03/01/2026'}]
        mortgages = [{'grantor': 'DOE JANE', 'grantee': 'VETERANS UNITED HOME LOANS',
                      'record_date': '03/01/2026', 'mortgage_value': '250000'}]
        _match_mortgages(deeds, mortgages)
        self.assertEqual(deeds[0]['mortgage_originator'], 'VETERANS UNITED HOME LOANS')


class ParseRowMortgageTests(unittest.TestCase):
    def test_includes_mortgage_value(self):
        session = CountyGovSession.__new__(CountyGovSession)
        raw = {'iID': '123', 'Name1': 'A', 'Name2': 'B', 'itNAME': 'Mortgage',
               'iRECORDED': '2026-03-15T00:00:00', 'iDESC': '', 'bkNAME': '',
               'iNUMBER': '', 'bktNAME': '', 'iPAGES': 0, 'itID': 0,
               'idVALUE_MORT': 280000.0, 'idVALUE_SUBDIV': ''}
        result = session._parse_row(raw)
        self.assertEqual(result['mortgage_value'], '280000.0')

    def test_zero_mortgage_filtered(self):
        session = CountyGovSession.__new__(CountyGovSession)
        raw = {'iID': '123', 'Name1': 'A', 'Name2': 'B', 'itNAME': 'Deed',
               'iRECORDED': '2026-03-15T00:00:00', 'iDESC': '', 'bkNAME': '',
               'iNUMBER': '', 'bktNAME': '', 'iPAGES': 0, 'itID': 0,
               'idVALUE_MORT': 0, 'idVALUE_SUBDIV': ''}
        result = session._parse_row(raw)
        self.assertEqual(result['mortgage_value'], '')
