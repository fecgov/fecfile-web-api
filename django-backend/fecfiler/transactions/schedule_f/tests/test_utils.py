from django.test import TestCase
from fecfiler.transactions.schedule_f.utils import add_schedule_f_contact_fields
from fecfiler.transactions.tests.test_utils import get_test_transaction
from fecfiler.committee_accounts.models import CommitteeAccount


class ScheduleFUtilsTestCase(TestCase):
    schedule_f_transaction_type = "COORDINATED_PARTY_EXPENDITURES"

    def test_contacts_to_representation(self):
        committee = CommitteeAccount.objects.create(committee_id="C00000000")
        instance = get_test_transaction(self.schedule_f_transaction_type, committee)

        representation = dict(
            transaction_type_identifier=self.schedule_f_transaction_type
        )

        add_schedule_f_contact_fields(instance, representation)

        self.assertEquals(
            representation["transaction_type_identifier"],
            self.schedule_f_transaction_type,
        )
        self.assertEquals(representation["payee_last_name"], "1 last name")
        self.assertEquals(representation["payee_candidate_last_name"], "2 last name")
        self.assertEquals(representation["payee_candidate_state"], "2 candidate state")
        self.assertEquals(representation["payee_candidate_id_number"], "2 candidate id")
        self.assertEquals(
            representation["subordinate_committee_id_number"], "3 committee id"
        )
        self.assertEquals(representation["subordinate_committee_name"], "3 name")
