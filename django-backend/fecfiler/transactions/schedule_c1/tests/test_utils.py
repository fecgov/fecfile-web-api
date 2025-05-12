from django.test import TestCase
from fecfiler.transactions.schedule_c1.utils import add_schedule_c1_contact_fields
from fecfiler.transactions.tests.test_utils import get_test_transaction


class ScheduleC1UtilsTestCase(TestCase):

    def test_contacts_to_representation(self):

        instance = get_test_transaction('C1_LOAN_AGREEMENT')

        representation = dict(
            transaction_type_identifier='C1_LOAN_AGREEMENT'
        )

        add_schedule_c1_contact_fields(instance, representation)

        self.assertEqual(
            representation['transaction_type_identifier'], 'C1_LOAN_AGREEMENT'
        )
        self.assertEqual(representation['lender_organization_name'], '1 name')
        self.assertEqual(representation['lender_zip'], '1 zip')
