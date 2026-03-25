from django.test import TestCase
from django.core.management import call_command
from django.contrib.sessions.models import Session
from django.utils import timezone
from fecfiler.committee_accounts.models import CommitteeAccount

COMMITTEE_ID_TO_DISABLE = "C12345678"
OTHER_COMMITTEE_ID = "C87654321"


class DisableCommitteeAccountCommandTest(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(
            committee_id=COMMITTEE_ID_TO_DISABLE
        )
        self.other_committee = CommitteeAccount.objects.create(
            committee_id=OTHER_COMMITTEE_ID
        )

    def test_disable_committee_command(self):
        s1 = Session.objects.create(
            session_key="target_session",
            expire_date=timezone.now() + timezone.timedelta(days=1),
        )
        s1.session_data = Session.objects.encode(
            {"committee_id": COMMITTEE_ID_TO_DISABLE}
        )
        s1.save()

        s2 = Session.objects.create(
            session_key="safe_session",
            expire_date=timezone.now() + timezone.timedelta(days=1),
        )
        s2.session_data = Session.objects.encode({"committee_id": OTHER_COMMITTEE_ID})
        s2.save()

        self.assertEqual(Session.objects.count(), 2)

        call_command("disable_committee_account", COMMITTEE_ID_TO_DISABLE)
        self.committee.refresh_from_db()
        self.other_committee.refresh_from_db()
        self.assertIsNotNone(self.committee.disabled)
        self.assertFalse(Session.objects.filter(session_key="target_session").exists())
        self.assertIsNone(self.other_committee.disabled)
        self.assertTrue(Session.objects.filter(session_key="safe_session").exists())

    def test_disable_non_existent_committee(self):
        try:
            call_command("disable_committee_account", "C00000000")
        except Exception as e:
            self.fail(f"Command crashed with error: {e}")
