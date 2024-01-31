from django.test import TestCase
from fecfiler.transactions.schedule_c.utils import add_schedule_c_contact_fields
from fecfiler.transactions.tests.test_utils import get_test_transaction


class ScheduleCUtilsTestCase(TestCase):

    def test_contacts_to_representation(self):

        instance = get_test_transaction('LOAN_RECEIVED_FROM_INDIVIDUAL')

        representation = dict(
            transaction_type_identifier='LOAN_RECEIVED_FROM_INDIVIDUAL'
        )

        add_schedule_c_contact_fields(instance, representation)

        self.assertEquals(
            representation['transaction_type_identifier'], 'LOAN_RECEIVED_FROM_INDIVIDUAL'
        )
        self.assertEquals(representation['lender_last_name'], '1 last name')
        self.assertEquals(representation['lender_candidate_last_name'], '2 last name')
