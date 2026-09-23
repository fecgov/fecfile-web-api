from random import choice
from fecfiler.user.models import User
from fecfiler.transactions.views import TransactionViewSet
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3, create_form3x
from fecfiler.contacts.tests.utils import (
    create_test_committee_contact,
    create_test_individual_contact,
    create_test_candidate_contact,
    create_test_organization_contact,
)
from fecfiler.transactions.tests.utils import (
    create_schedule_a,
)
from fecfiler.shared.viewset_test import FecfilerViewSetTest
import structlog

logger = structlog.get_logger(__name__)


schedule_a_test_mappings = [
    ["INDIVIDUAL_RECEIPT", "IND", {"F3": "SA11AI", "F3X": "SA11AI"}],
    ["TRIBAL_RECEIPT", "IND", {"F3": "SA11AI", "F3X": "SA11AI"}],
    ["OFFSET_TO_OPERATING_EXPENDITURES", "ORG", {"F3": "SA14", "F3X": "SA15"}],
    ["OTHER_RECEIPT", "COM", {"F3": "SA15", "F3X": "SA17"}],
]


class TransactionLineNumberAnnotationTestCase(FecfilerViewSetTest):
    json_content_type = "application/json"

    @classmethod
    def setUpClass(cls):
        return super().setUpClass()

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(email="test@fec.gov", username="gov")
        super().set_default_user(self.user)
        super().set_default_committee(self.committee)
        super().setUp()

        self.f3x_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.f3_report = create_form3(self.committee, "2024-03-01", "2024-04-01", {})

        self.contact_individual = create_test_individual_contact(
            "last name",
            "First name",
            self.committee.id,
            {
                "street_1": "123 test street",
                "city": "testville",
                "state": "AK",
                "zip": "12345",
            },
        )
        self.contact_candidate = create_test_candidate_contact(
            "last name", "First name", self.committee.id, "H8MA03131", "S", "AK", "01"
        )
        self.contact_committee = create_test_committee_contact(
            "TEST COMMITTEES UNITED",
            "C12344321",
            self.committee.id,
            {"street_1": "Test St", "city": "Testville", "state": "IL", "zip": "12345"},
        )
        self.test_org_contact = create_test_organization_contact(
            "test-org-name1",
            self.committee.id,
            {
                "street_1": "test_sa1",
                "street_2": "test_sa2",
                "city": "test_c1",
                "state": "AL",
                "zip": "12345",
                "telephone": "555-555-5555",
                "country": "USA",
            },
        )

        self.view = TransactionViewSet()

    def get_contact_for_entity_type(self, entity_type: str | list):
        if entity_type.__class__ is type[list]:
            entity_type = choice(entity_type)

        match entity_type:
            case "IND":
                return self.contact_individual
            case "COM":
                return self.contact_committee
            case "ORG":
                return self.test_org_contact
            case "CAN":
                return self.contact_candidate

    def get_report_for_type(self, report_type):
        match report_type:
            case "F3":
                return self.f3_report
            case "F3X":
                return self.f3x_report

    def get_request(self, path="api/v1/transactions", params={}):
        request = self.build_viewset_get_request(path)
        request.query_params = params
        request.data = {}
        return request

    def test_sch_a_line_number_annotation(self):
        for tti, entity_type, line_number_mappings in schedule_a_test_mappings:
            for report_type in line_number_mappings.keys():
                report = self.get_report_for_type(report_type)
                new_transaction = create_schedule_a(
                    tti,
                    self.committee,
                    self.get_contact_for_entity_type(entity_type),
                    self.f3x_report.coverage_from_date,
                    "202.00",
                    report=report
                )

                self.view.request = self.get_request(
                    params={
                        "report_id": report.id,
                    }
                )
                queryset = self.view.get_queryset()
                saved_transaction = queryset.get(id=new_transaction.id)
                self.assertEqual(
                    saved_transaction.form_type,
                    line_number_mappings[report_type]
                )
