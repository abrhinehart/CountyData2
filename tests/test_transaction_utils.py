import unittest

from utils.transaction_utils import classify_transaction_type, extract_acres


class TransactionTypeTests(unittest.TestCase):
    def test_builder_to_builder_takes_priority(self):
        result = classify_transaction_type(
            grantor_builder_id=1,
            grantee_builder_id=2,
            grantor_land_banker_id=None,
            grantee_land_banker_id=None,
        )
        self.assertEqual(result, 'Builder to Builder')

    def test_builder_purchase_when_grantee_builder_matches(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=1,
            grantor_land_banker_id=None,
            grantee_land_banker_id=None,
        )
        self.assertEqual(result, 'Builder Purchase')

    def test_land_banker_purchase_when_grantee_land_banker_matches(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=None,
            grantor_land_banker_id=None,
            grantee_land_banker_id=9,
        )
        self.assertEqual(result, 'Land Banker Purchase')

    def test_builder_purchase_beats_land_banker_grantor(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=1,
            grantor_land_banker_id=9,
            grantee_land_banker_id=None,
        )
        self.assertEqual(result, 'Builder Purchase')

    def test_house_sale_when_no_tracked_entities_match(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=None,
            grantor_land_banker_id=None,
            grantee_land_banker_id=None,
        )
        self.assertEqual(result, 'House Sale')

    def test_association_transfer_overrides_default_house_sale(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=None,
            grantor_land_banker_id=None,
            grantee_land_banker_id=None,
            grantee='Freedom Crossings Preserve Property Owners Association Inc',
        )
        self.assertEqual(result, 'Association Transfer')

    def test_cdd_transfer_overrides_default_house_sale(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=None,
            grantor_land_banker_id=None,
            grantee_land_banker_id=None,
            grantee='Caldera Community Development District',
        )
        self.assertEqual(result, 'CDD Transfer')

    def test_correction_record_overrides_builder_purchase(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=1,
            grantor_land_banker_id=None,
            grantee_land_banker_id=None,
            instrument='Quit Claim Deed',
            export_legal_desc='TO CORRECT',
        )
        self.assertEqual(result, 'Correction / Quit Claim')

    def test_raw_land_purchase_requires_non_platted_builder_acquisition(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=1,
            grantor_land_banker_id=None,
            grantee_land_banker_id=None,
            export_legal_desc='Section: 19 Township: 4N Range: 23 Legal Remarks: COMM AT SWC (MULTIPLE PARCELS)',
            subdivision=None,
            county_parse={
                'section_values': ['19'],
                'township_values': ['4N'],
                'range_values': ['23'],
                'legal_remarks_values': ['COMM AT SWC (MULTIPLE PARCELS)'],
            },
        )
        self.assertEqual(result, 'Raw Land Purchase')

    def test_build_to_rent_purchase_when_grantee_land_banker_is_btr(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=None,
            grantor_land_banker_id=None,
            grantee_land_banker_id=9,
            grantee_land_banker_category='btr',
        )
        self.assertEqual(result, 'Build-to-Rent Purchase')

    def test_land_banker_purchase_when_category_is_land_banker(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=None,
            grantor_land_banker_id=None,
            grantee_land_banker_id=9,
            grantee_land_banker_category='land_banker',
        )
        self.assertEqual(result, 'Land Banker Purchase')

    def test_land_banker_purchase_when_category_is_developer(self):
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=None,
            grantor_land_banker_id=None,
            grantee_land_banker_id=9,
            grantee_land_banker_category='developer',
        )
        self.assertEqual(result, 'Land Banker Purchase')

    def test_land_banker_purchase_when_category_is_none(self):
        """Backwards compat: no category defaults to Land Banker Purchase."""
        result = classify_transaction_type(
            grantor_builder_id=None,
            grantee_builder_id=None,
            grantor_land_banker_id=None,
            grantee_land_banker_id=9,
            grantee_land_banker_category=None,
        )
        self.assertEqual(result, 'Land Banker Purchase')

    def test_extract_acres_handles_mixed_number(self):
        self.assertEqual(extract_acres('TRACT A CONTAINING 2 1/2 ACRES MOL'), 2.5)


if __name__ == '__main__':
    unittest.main()
