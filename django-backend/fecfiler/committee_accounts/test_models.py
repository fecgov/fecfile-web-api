from django.apps import apps
from django.test import TestCase
from .models import CommitteeAccount, CommitteeOwnedModel, Membership
from fecfiler.user.models import User
from django.core.exceptions import ValidationError


class CommitteeAccountTestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_committee_account = CommitteeAccount(
            committee_id="C87654321",
        )

    def test_get_contact(self):
        committee_account = CommitteeAccount.objects.get(committee_id="C12345678")
        self.assertEquals(committee_account.committee_id, "C12345678")

    def test_save_and_delete(self):
        self.valid_committee_account.save()
        committee_account_from_db = CommitteeAccount.objects.get(committee_id="C87654321")
        self.assertIsInstance(committee_account_from_db, CommitteeAccount)
        self.assertEquals(committee_account_from_db.committee_id, "C87654321")
        committee_account_from_db.delete()
        self.assertRaises(
            CommitteeAccount.DoesNotExist,
            CommitteeAccount.objects.get,
            committee_id="C87654321",
        )

        soft_deleted_committee_account = CommitteeAccount.all_objects.get(
            committee_id="C87654321"
        )
        self.assertEquals(soft_deleted_committee_account.committee_id, "C87654321")
        self.assertIsNotNone(soft_deleted_committee_account.deleted)
        soft_deleted_committee_account.hard_delete()
        self.assertRaises(
            CommitteeAccount.DoesNotExist,
            CommitteeAccount.all_objects.get,
            committee_id="C87654321",
        )

    def test_all_models_include_committee_owned_mixin(self):
        ignore_list = [
            "Permission",
            "Group",
            "ContentType",
            "Session",
            "CommitteeAccount",
            "Membership",
            "Form3X",
            "Form24",
            "Form99",
            "Form1M",
            "ReportTransaction",
            "ScheduleA",
            "OverTwoHundredTypesScheduleA",
            "ScheduleB",
            "OverTwoHundredTypesScheduleB",
            "ScheduleC",
            "ScheduleC1",
            "ScheduleC2",
            "ScheduleD",
            "ScheduleE",
            "ScheduleF",
            "DotFEC",
            "UploadSubmission",
            "WebPrintSubmission",
            "User",
        ]
        app_models = apps.get_models()

        for model in app_models:
            with self.subTest(model=model):
                if model.__name__ not in ignore_list:
                    self.assertTrue(
                        issubclass(model, CommitteeOwnedModel),
                        f"{model.__name__} does not include CommitteeOwnedModel mixin.",
                    )


class MembershipTestCase(TestCase):
    def setUp(self):
        self.admin1 = User.objects.create_user(
            email="admin1@admin.com", user_id="5e3c145f-a813-46c7-af5a-5739304acc27"
        )
        self.admin2 = User.objects.create_user(
            email="admin2@admin.com", user_id="5e3c145f-a813-46c7-af5a-5739304acc26"
        )
        self.user = User.objects.create_user(
            email="user@user.com", user_id="5e3c145f-a813-46c7-af5a-5739304acc25"
        )

        self.admin1_membership = Membership.objects.create(
            user=self.admin1, role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR
        )
        self.admin2_membership = Membership.objects.create(
            user=self.admin2, role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR
        )
        self.user_membership = Membership.objects.create(
            user=self.user, role=Membership.CommitteeRole.MANAGER
        )

    def test_cannot_delete_when_two_admins(self):
        with self.assertRaises(ValidationError) as cm:
            self.admin1_membership.delete()
        self.assertEqual(
            str(cm.exception),
            "['Cannot delete a COMMITTEE_ADMINISTRATOR "
            "when there are 2 or fewer remaining.']",
        )

    def test_can_delete_non_admin(self):
        self.user_membership.delete()
        self.assertFalse(Membership.objects.filter(id=self.user_membership.id).exists())

    def test_can_delete_admin_when_more_than_two(self):
        admin3 = User.objects.create_user(
            email="admin3@admin.com", user_id="5e3c145f-a813-46c7-af5a-5739304acc24"
        )
        admin3_membership = Membership.objects.create(
            user=admin3, role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR
        )
        admin3_membership.delete()
        self.assertFalse(Membership.objects.filter(id=admin3.id).exists())
