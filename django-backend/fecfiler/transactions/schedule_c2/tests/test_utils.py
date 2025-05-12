from django.test import TestCase
from fecfiler.transactions.schedule_c2.utils import add_schedule_c2_contact_fields
from fecfiler.transactions.tests.test_utils import get_test_transaction


class ScheduleC2UtilsTestCase(TestCase):

    def test_contacts_to_representation(self):

        instance = get_test_transaction('C2_LOAN_GUARANTOR')

        representation = dict(
            transaction_type_identifier='C2_LOAN_GUARANTOR'
        )

        add_schedule_c2_contact_fields(instance, representation)

        self.assertEqual(
            representation['transaction_type_identifier'], 'C2_LOAN_GUARANTOR'
        )
        self.assertEqual(representation['guarantor_last_name'], '1 last name')
        self.assertEqual(representation['guarantor_zip'], '1 zip')
