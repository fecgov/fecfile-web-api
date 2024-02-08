from django.test import TestCase
from fecfiler.transactions.schedule_b.utils import add_schedule_b_contact_fields
from fecfiler.transactions.tests.test_utils import get_test_transaction


class ScheduleBUtilsTestCase(TestCase):

    def test_contacts_to_representation(self):

        instance = get_test_transaction('REFUND_INDIVIDUAL_CONTRIBUTION')

        representation = dict(
            transaction_type_identifier='REFUND_INDIVIDUAL_CONTRIBUTION'
        )

        add_schedule_b_contact_fields(instance, representation)

        self.assertEquals(
            representation['transaction_type_identifier'],
            'REFUND_INDIVIDUAL_CONTRIBUTION'
        )
        self.assertEquals(representation['payee_last_name'], '1 last name')
        self.assertEquals(
            representation['beneficiary_candidate_last_name'], '2 last name'
        )
        self.assertEquals(representation['beneficiary_committee_name'], '3 name')

        # Test donor committee override
        instance.transaction_type_identifier = 'CONTRIBUTION_TO_CANDIDATE'
        instance.contact_3 = None
        add_schedule_b_contact_fields(instance, representation)
        self.assertEquals(representation['beneficiary_committee_name'], '1 name')
