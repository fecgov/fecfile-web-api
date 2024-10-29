from decimal import Decimal
from django.test import TestCase
from .models import F3xLine6aOverride
from datetime import datetime
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.contacts.tests.utils import create_test_individual_contact
from fecfiler.web_services.summary.tasks import CalculationState
from fecfiler.reports.models import Report


class F3xLine6aOverrideTestCase(TestCase):
    fixtures = ["test_f3x_line6a_overrides"]

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )

    def test_f3x_line6a_override_crud(self):
        self.test_f3x_line6a_override = F3xLine6aOverride(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4",
            year="2024",
            cash_on_hand=501.40,
        )
        self.test_f3x_line6a_override.save()

        override_2024 = F3xLine6aOverride.objects.get(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        )
        self.assertEquals(override_2024.year, "2024")
        self.assertEquals(override_2024.cash_on_hand, Decimal("501.40"))

        F3xLine6aOverride.objects.filter(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        ).update(cash_on_hand=300.00)
        override_2024 = F3xLine6aOverride.objects.get(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        )
        self.assertEquals(override_2024.cash_on_hand, 300.00)

        F3xLine6aOverride.objects.filter(
            id="422095b3-e0a7-4499-9d2c-5efb3858fce4"
        ).delete()

        with self.assertRaises(F3xLine6aOverride.DoesNotExist):
            F3xLine6aOverride.objects.get(
                id="422095b3-e0a7-4499-9d2c-5efb3858fce4",
            )

    def test_marks_future_reports_calculation_status_none(self):
        f3x1 = create_form3x(
            self.committee,
            datetime.strptime("2015-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2015-02-28", "%Y-%m-%d").date(),
            {},
            "12C",
        )
        f3x2 = create_form3x(
            self.committee,
            datetime.strptime("2020-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2020-02-28", "%Y-%m-%d").date(),
            {},
            "12C",
        )
        Report.objects.update(calculation_status=CalculationState.SUCCEEDED)

        F3xLine6aOverride.objects.create(
            year="2016",
            cash_on_hand=100,
        )

        self.assertIsNotNone(Report.objects.get(pk=f3x1.id).calculation_status)
        self.assertIsNone(Report.objects.get(pk=f3x2.id).calculation_status)
