from django.test import TestCase
from ..models import CashOnHandYearly
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.web_services.summary.tasks import CalculationState
from fecfiler.reports.models import Report


class CashOnHandYearlyTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")

    def test_calcualtion_status_flag(self):
        f3x1 = create_form3x(
            self.committee,
            "2005-01-01",
            "2005-01-30",
        )
        f3x2 = create_form3x(
            self.committee,
            "2005-02-01",
            "2005-02-28",
        )
        Report.objects.update(calculation_status=CalculationState.SUCCEEDED)

        CashOnHandYearly.objects.create(
            committee_account=self.committee,
            year="2016",
            cash_on_hand=100,
        )

        self.assertIsNone(Report.objects.get(pk=f3x1.id).calculation_status)
        self.assertIsNone(Report.objects.get(pk=f3x2.id).calculation_status)

    def test_permissions(self):
        CashOnHandYearly.objects.create(
            committee_account=self.committee,
            year="2016",
            cash_on_hand=100,
        )
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        other_committees_coh = CashOnHandYearly.objects.filter(
            committee_account=other_committee
        ).first()
        self.assertIsNone(other_committees_coh)
