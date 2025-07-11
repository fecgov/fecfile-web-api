from django.test import TestCase
from fecfiler.transactions.schedule_e.utils import add_schedule_e_contact_fields
from fecfiler.transactions.tests.test_utils import get_test_transaction
from fecfiler.transactions.schedule_e.models import ScheduleE


class ScheduleEUtilsTestCase(TestCase):

    def test_contacts_to_representation(self):

        instance = get_test_transaction("INDEPENDENT_EXPENDITURE")

        representation = dict(transaction_type_identifier="INDEPENDENT_EXPENDITURE")

        add_schedule_e_contact_fields(instance, representation)

        self.assertEqual(
            representation["transaction_type_identifier"], "INDEPENDENT_EXPENDITURE"
        )
        self.assertEqual(representation["payee_last_name"], "1 last name")
        self.assertEqual(representation["so_candidate_last_name"], "2 last name")
        self.assertEqual(representation["so_candidate_state"], "2 candidate state")

    def test_contacts_to_representation_primary_presidential(self):

        instance = get_test_transaction("INDEPENDENT_EXPENDITURE")
        instance.schedule_e = ScheduleE(election_code="P2024", so_candidate_state="CA")
        instance.contact_2.candidate_office = "P"

        representation = dict(transaction_type_identifier="INDEPENDENT_EXPENDITURE")

        add_schedule_e_contact_fields(instance, representation)

        self.assertEqual(
            representation["transaction_type_identifier"], "INDEPENDENT_EXPENDITURE"
        )
        self.assertEqual(representation["payee_last_name"], "1 last name")
        self.assertEqual(representation["so_candidate_last_name"], "2 last name")
        self.assertEqual(representation["so_candidate_state"], "CA")
