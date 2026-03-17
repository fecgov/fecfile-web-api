from django.test import TestCase
from django.core.management import call_command
from fecfiler.committee_accounts.models import CommitteeAccount

COMMITTEE_ID = "C12345678"


class EnableCommitteeAccountCommandTest(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id=COMMITTEE_ID)
        self.committee.delete()

        self.assertFalse(
            CommitteeAccount.objects.filter(committee_id=COMMITTEE_ID).exists()
        )

    def test_enable_committee_command(self):
        call_command("enable_committee_account", COMMITTEE_ID)

        self.assertTrue(
            CommitteeAccount.objects.filter(committee_id=COMMITTEE_ID).exists()
        )

        re_enabled_committee = CommitteeAccount.objects.get(committee_id=COMMITTEE_ID)
        self.assertIsNone(re_enabled_committee.deleted)

    def test_enable_non_existent_committee(self):
        try:
            call_command("enable_committee_account", "C00000000")
        except Exception as e:
            self.fail(f"Command crashed on non-existent ID: {e}")
