import unittest

from utils.transaction_utils import classify_transaction_type


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


if __name__ == '__main__':
    unittest.main()
