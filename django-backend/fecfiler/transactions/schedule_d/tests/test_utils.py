from django.test import TestCase
from fecfiler.transactions.schedule_d.utils import add_schedule_d_contact_fields
from fecfiler.transactions.tests.test_utils import get_test_transaction


class ScheduleDUtilsTestCase(TestCase):

    def test_contacts_to_representation(self):

        instance = get_test_transaction('DEBT_OWED_TO_COMMITTEE')

        representation = dict(
            transaction_type_identifier='DEBT_OWED_TO_COMMITTEE'
        )

        add_schedule_d_contact_fields(instance, representation)

        self.assertEqual(
            representation['transaction_type_identifier'], 'DEBT_OWED_TO_COMMITTEE'
        )
        self.assertEqual(representation['creditor_last_name'], '1 last name')
        self.assertEqual(representation['creditor_zip'], '1 zip')
