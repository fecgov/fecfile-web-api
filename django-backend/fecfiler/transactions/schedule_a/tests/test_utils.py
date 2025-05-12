from django.test import TestCase
from fecfiler.transactions.schedule_a.utils import add_schedule_a_contact_fields
from fecfiler.transactions.tests.test_utils import get_test_transaction


class ScheduleAUtilsTestCase(TestCase):

    def test_contacts_to_representation(self):

        instance = get_test_transaction()

        representation = dict(
            transaction_type_identifier='INDIVIDUAL_RECEIPT'
        )

        add_schedule_a_contact_fields(instance, representation)

        self.assertEqual(
            representation['transaction_type_identifier'], 'INDIVIDUAL_RECEIPT'
        )
        self.assertEqual(representation['contributor_last_name'], '1 last name')
        self.assertEqual(representation['donor_candidate_last_name'], '2 last name')
        self.assertEqual(representation['donor_committee_name'], '3 name')

        # Test donor committee override
        instance.transaction_type_identifier = 'PARTY_RECEIPT'
        instance.contact_3 = None
        add_schedule_a_contact_fields(instance, representation)
        self.assertEqual(representation['donor_committee_name'], '1 name')
