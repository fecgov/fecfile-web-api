from django.test import TestCase
from fecfiler.transactions.schedule_e.utils import add_schedule_e_contact_fields
from fecfiler.transactions.tests.test_utils import get_test_transaction


class ScheduleEUtilsTestCase(TestCase):

    def test_contacts_to_representation(self):

        instance = get_test_transaction('INDEPENDENT_EXPENDITURE')

        representation = dict(
            transaction_type_identifier='INDEPENDENT_EXPENDITURE'
        )

        add_schedule_e_contact_fields(instance, representation)

        self.assertEquals(
            representation['transaction_type_identifier'], 'INDEPENDENT_EXPENDITURE'
        )
        self.assertEquals(representation['payee_last_name'], '1 last name')
        self.assertEquals(representation['so_candidate_last_name'], '2 last name')
