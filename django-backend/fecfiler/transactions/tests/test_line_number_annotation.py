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
    create_schedule_b,
    create_loan,
    create_debt,
    create_schedule_f,
    create_ie,
)
from fecfiler.shared.viewset_test import FecfilerViewSetTest
import structlog

logger = structlog.get_logger(__name__)

# If this is set to False, the unit tests will be run with a subset
# of transaction types in order to save time.
RUN_ALL_TRANSACTION_TYPES = False


# IF THERE IS A MISMATCH, YOU MUST CHECK THE SPEC SHEET.  THIS IS NOT A SOURCE OF TRUTH


unitemized_f3_and_f3x = {"F3": "SA11AI", "F3X": "SA11AI", "Unitemized": "SA11AII"}
unitemized_f3x = {"F3X": "SA11AI", "Unitemized": "SA11AII"}

schedule_a_test_mappings = [
    ["INDIVIDUAL_RECEIPT", "IND", unitemized_f3_and_f3x],
    ["TRIBAL_RECEIPT", "ORG", unitemized_f3_and_f3x],
    ["PARTNERSHIP_RECEIPT", "ORG", unitemized_f3_and_f3x],
    ["PARTNERSHIP_ATTRIBUTION", "IND", unitemized_f3_and_f3x],
    ["IN_KIND_RECEIPT", "IND", unitemized_f3x],
    ["RETURN_RECEIPT", "IND", unitemized_f3_and_f3x],
    ["EARMARK_RECEIPT", "IND", unitemized_f3x],
    ["EARMARK_MEMO", "IND", unitemized_f3x],
    ["CONDUIT_EARMARK_RECEIPT_DEPOSITED", "IND", unitemized_f3x],
    ["CONDUIT_EARMARK_RECEIPT_UNDEPOSITED", "IND", unitemized_f3x],
    ["RECEIPT_FROM_UNREGISTERED_ORGANIZATION", "ORG", unitemized_f3_and_f3x],
    ["RECEIPT_FROM_UNREGISTERED_ORGANIZATION_RETURN", "ORG", unitemized_f3_and_f3x],
    ["PARTY_RECEIPT", "COM", {"F3": "SA11B", "F3X": "SA11B"}],
    ["PARTY_RETURN", "COM", {"F3": "SA11B", "F3X": "SA11B"}],
    ["PARTY_IN_KIND_RECEIPT", "COM", {"F3X": "SA11B"}],
    ["PAC_IN_KIND_RECEIPT", "COM", {"F3X": "SA11C"}],
    ["PAC_RECEIPT", "COM", {"F3": "SA11C", "F3X": "SA11C"}],
    ["PAC_EARMARK_RECEIPT", "COM", {"F3X": "SA11C"}],
    ["PAC_EARMARK_MEMO", "COM", {"F3X": "SA11C"}],
    ["PAC_CONDUIT_EARMARK_RECEIPT_DEPOSITED", "COM", {"F3X": "SA11C"}],
    ["PAC_CONDUIT_EARMARK_RECEIPT_UNDEPOSITED", "COM", {"F3X": "SA11C"}],
    ["PAC_RETURN", "COM", {"F3": "SA11C", "F3X": "SA11C"}],
    ["CONTRIBUTION_FROM_CANDIDATE", "CAN", {"F3": "SA11D"}],
    ["TRANSFER", "COM", {"F3X": "SA12"}],
    ["JOINT_FUNDRAISING_TRANSFER", "COM", {"F3X": "SA12"}],
    ["INDIVIDUAL_JF_TRANSFER_MEMO", "IND", {"F3X": "SA12"}],
    ["PARTY_JF_TRANSFER_MEMO", "COM", {"F3X": "SA12"}],
    ["PAC_JF_TRANSFER_MEMO", "COM", {"F3X": "SA12"}],
    ["TRIBAL_JF_TRANSFER_MEMO", "ORG", {"F3X": "SA12"}],
    ["PARTNERSHIP_JF_TRANSFER_MEMO", "ORG", {"F3X": "SA12"}],
    ["PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO", "IND", {"F3X": "SA12"}],
    ["IN_KIND_TRANSFER", "COM", {"F3X": "SA12"}],
    ["IN_KIND_TRANSFER_FEDERAL_ELECTION_ACTIVITY", "COM", {"F3X": "SA12"}],
    ["JF_TRANSFER_NATIONAL_PARTY_RECOUNT_ACCOUNT", "COM", {"F3X": "SA17"}],
    ["INDIVIDUAL_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO", "IND", {"F3X": "SA17"}],
    ["PAC_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO", "COM", {"F3X": "SA17"}],
    ["TRIBAL_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO", "IND", {"F3X": "SA17"}],  # noqa: E501
    ["JF_TRANSFER_NATIONAL_PARTY_CONVENTION_ACCOUNT", "COM", {"F3X": "SA17"}],
    ["INDIVIDUAL_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO", "IND", {"F3X": "SA17"}],
    ["PAC_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO", "COM", {"F3X": "SA17"}],
    ["TRIBAL_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO", "IND", {"F3X": "SA17"}],  # noqa: E501
    ["JF_TRANSFER_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT", "COM", {"F3X": "SA17"}],
    ["INDIVIDUAL_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO", "IND", {"F3X": "SA17"}],
    ["PAC_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO", "COM", {"F3X": "SA17"}],
    ["TRIBAL_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO", "IND", {"F3X": "SA17"}],  # noqa: E501
    ["REFUND_TO_FEDERAL_CANDIDATE", "COM", {"F3X": "SA16"}],
    ["REFUND_TO_OTHER_POLITICAL_COMMITTEE", "COM", {"F3X": "SA16"}],
    ["REFUND_TO_UNREGISTERED_COMMITTEE", "ORG", {"F3X": "SA16"}],
    ["OFFSET_TO_OPERATING_EXPENDITURES", "ORG", {"F3": "SA14", "F3X": "SA15"}],
    ["OTHER_RECEIPT", "COM", {"F3": "SA15", "F3X": "SA17"}],
    ["INDIVIDUAL_RECEIPT_NON_CONTRIBUTION_ACCOUNT", "IND", {"F3X": "SA17"}],
    ["OTHER_COMMITTEE_NON_CONTRIBUTION_ACCOUNT", "COM", {"F3X": "SA17"}],
    ["BUSINESS_LABOR_NON_CONTRIBUTION_ACCOUNT", "ORG", {"F3X": "SA17"}],
    ["INDIVIDUAL_RECOUNT_RECEIPT", "IND", {"F3": "SA15", "F3X": "SA17"}],
    ["PARTY_RECOUNT_RECEIPT", "COM", {"F3": "SA15", "F3X": "SA17"}],
    ["PAC_RECOUNT_RECEIPT", "COM", {"F3": "SA15", "F3X": "SA17"}],
    ["TRIBAL_RECOUNT_RECEIPT", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_RECOUNT_ACCOUNT_RECEIPT", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_ATTRIBUTION_RECOUNT_ACCOUNT_RECEIPT_MEMO", "IND", {"F3X": "SA17"}],  # noqa: E501
    ["INDIVIDUAL_NATIONAL_PARTY_RECOUNT_ACCOUNT", "IND", {"F3X": "SA17"}],
    ["PARTY_NATIONAL_PARTY_RECOUNT_ACCOUNT", "COM", {"F3X": "SA17"}],
    ["PAC_NATIONAL_PARTY_RECOUNT_ACCOUNT", "COM", {"F3X": "SA17"}],
    ["TRIBAL_NATIONAL_PARTY_RECOUNT_ACCOUNT", "ORG", {"F3X": "SA17"}],
    ["INDIVIDUAL_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT", "IND", {"F3X": "SA17"}],
    ["PARTY_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT", "COM", {"F3X": "SA17"}],
    ["PAC_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT", "COM", {"F3X": "SA17"}],
    ["TRIBAL_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT", "ORG", {"F3X": "SA17"}],
    ["INDIVIDUAL_NATIONAL_PARTY_CONVENTION_ACCOUNT", "IND", {"F3X": "SA17"}],
    ["PARTY_NATIONAL_PARTY_CONVENTION_ACCOUNT", "COM", {"F3X": "SA17"}],
    ["PAC_NATIONAL_PARTY_CONVENTION_ACCOUNT", "COM", {"F3X": "SA17"}],
    ["TRIBAL_NATIONAL_PARTY_CONVENTION_ACCOUNT", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_NATIONAL_PARTY_RECOUNT_ACCOUNT", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_NATIONAL_PARTY_CONVENTION_ACCOUNT", "ORG", {"F3X": "SA17"}],
    ["PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_RECOUNT_ACCOUNT_MEMO", "IND", {"F3X": "SA17"}],  # noqa: E501
    ["PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT_MEMO", "IND", {"F3X": "SA17"}],  # noqa: E501
    ["PARTNERSHIP_ATTRIBUTION_NATIONAL_PARTY_CONVENTION_ACCOUNT_MEMO", "IND", {"F3X": "SA17"}],  # noqa: E501
    ["EARMARK_RECEIPT_RECOUNT_ACCOUNT", "IND", {"F3X": "SA17"}],
    ["EARMARK_RECEIPT_CONVENTION_ACCOUNT", "IND", {"F3X": "SA17"}],
    ["EARMARK_RECEIPT_HEADQUARTERS_ACCOUNT", "IND", {"F3X": "SA17"}],
    ["EARMARK_MEMO_RECOUNT_ACCOUNT", "IND", {"F3X": "SA17"}],
    ["EARMARK_MEMO_CONVENTION_ACCOUNT", "IND", {"F3X": "SA17"}],
    ["EARMARK_MEMO_HEADQUARTERS_ACCOUNT", "IND", {"F3X": "SA17"}],
    ["LOAN_RECEIVED_FROM_INDIVIDUAL_RECEIPT", "IND", {"F3X": "SA13"}],
    ["LOAN_RECEIVED_FROM_BANK_RECEIPT", "ORG", {"F3X": "SA13"}],
    ["LOAN_REPAYMENT_RECEIVED", "COM", {"F3X": "SA14"}],
]

schedule_a_test_mappings_sampler = [
    ["LOAN_REPAYMENT_RECEIVED", "COM", {"F3X": "SA14"}],
    ["TRIBAL_RECOUNT_RECEIPT", "ORG", {"F3X": "SA17"}],
    ["PARTY_JF_TRANSFER_MEMO", "COM", {"F3X": "SA12"}],
    ["PAC_RETURN", "COM", {"F3": "SA11C", "F3X": "SA11C"}],
    ["CONTRIBUTION_FROM_CANDIDATE", "CAN", {"F3": "SA11D"}],
    ["PARTY_RECEIPT", "COM", {"F3": "SA11B", "F3X": "SA11B"}],
    ["EARMARK_MEMO", "IND", unitemized_f3x],
    ["CONDUIT_EARMARK_RECEIPT_DEPOSITED", "IND", unitemized_f3x],
]

schedule_b_test_mappings = [
    ["OPERATING_EXPENDITURE", "ORG", {"F3X": "SB21B"}],
    ["OPERATING_EXPENDITURE_VOID", "ORG", {"F3X": "SB21B"}],
    ["OTHER_DISBURSEMENT", "ORG", {"F3X": "SB29"}],
    ["OTHER_DISBURSEMENT_VOID", "COM", {"F3X": "SB29"}],
    ["OPERATING_EXPENDITURE_CREDIT_CARD_PAYMENT", "ORG", {"F3X": "SB21B"}],
    ["OPERATING_EXPENDITURE_PAYMENT_TO_PAYROLL", "ORG", {"F3X": "SB21B"}],
    ["OTHER_DISBURSEMENT_CREDIT_CARD_PAYMENT", "ORG", {"F3X": "SB29"}],
    ["OTHER_DISBURSEMENT_PAYMENT_TO_PAYROLL", "ORG", {"F3X": "SB29"}],
    ["OPERATING_EXPENDITURE_STAFF_REIMBURSEMENT", "IND", {"F3X": "SB21B"}],
    ["OTHER_DISBURSEMENT_STAFF_REIMBURSEMENT", "IND", {"F3X": "SB29"}],
    ["OPERATING_EXPENDITURE_CREDIT_CARD_PAYMENT_MEMO", "ORG", {"F3X": "SB21B"}],  # noqa: E501
    ["OPERATING_EXPENDITURE_STAFF_REIMBURSEMENT_MEMO", "ORG", {"F3X": "SB21B"}],  # noqa: E501
    ["OPERATING_EXPENDITURE_PAYMENT_TO_PAYROLL_MEMO", "IND", {"F3X": "SB21B"}],  # noqa: E501
    ["OTHER_DISBURSEMENT_PAYMENT_TO_PAYROLL_MEMO", "IND", {"F3X": "SB29"}],
    ["OTHER_DISBURSEMENT_CREDIT_CARD_PAYMENT_MEMO", "ORG", {"F3X": "SB29"}],
    ["OTHER_DISBURSEMENT_STAFF_REIMBURSEMENT_MEMO", "ORG", {"F3X": "SB29"}],
    ["TRANSFER_TO_AFFILIATES", "COM", {"F3X": "SB22"}],
    ["CONTRIBUTION_TO_CANDIDATE", "COM", {"F3X": "SB23"}],
    ["CONTRIBUTION_TO_CANDIDATE_VOID", "COM", {"F3X": "SB23"}],
    ["CONTRIBUTION_TO_OTHER_COMMITTEE", "COM", {"F3X": "SB23"}],
    ["CONTRIBUTION_TO_OTHER_COMMITTEE_VOID", "COM", {"F3X": "SB23"}],
    ["IN_KIND_CONTRIBUTION_TO_CANDIDATE", "ORG", {"F3X": "SB23"}],
    ["IN_KIND_CONTRIBUTION_TO_OTHER_COMMITTEE", "ORG", {"F3X": "SB23"}],
    ["NON_CONTRIBUTION_ACCOUNT_DISBURSEMENT", "ORG", {"F3X": "SB29"}],
    ["NON_CONTRIBUTION_ACCOUNT_CREDIT_CARD_PAYMENT", "ORG", {"F3X": "SB29"}],
    ["NON_CONTRIBUTION_ACCOUNT_PAYMENT_TO_PAYROLL", "ORG", {"F3X": "SB29"}],
    ["NON_CONTRIBUTION_ACCOUNT_STAFF_REIMBURSEMENT", "IND", {"F3X": "SB29"}],
    ["NON_CONTRIBUTION_ACCOUNT_CREDIT_CARD_PAYMENT_MEMO", "ORG", {"F3X": "SB29"}],
    ["NON_CONTRIBUTION_ACCOUNT_STAFF_REIMBURSEMENT_MEMO", "ORG", {"F3X": "SB29"}],
    ["NON_CONTRIBUTION_ACCOUNT_PAYMENT_TO_PAYROLL_MEMO", "IND", {"F3X": "SB29"}],
    ["INDIVIDUAL_REFUND_NON_CONTRIBUTION_ACCOUNT", "IND", {"F3X": "SB29"}],
    ["BUSINESS_LABOR_REFUND_NON_CONTRIBUTION_ACCOUNT", "ORG", {"F3X": "SB29"}],
    ["OTHER_COMMITTEE_REFUND_NON_CONTRIBUTION_ACCOUNT", "COM", {"F3X": "SB29"}],
    ["RECOUNT_ACCOUNT_DISBURSEMENT", "ORG", {"F3X": "SB29"}],
    ["NATIONAL_PARTY_RECOUNT_ACCOUNT_DISBURSEMENT", "ORG", {"F3X": "SB29"}],
    ["NATIONAL_PARTY_HEADQUARTERS_ACCOUNT_DISBURSEMENT", "ORG", {"F3X": "SB21B"}],
    ["NATIONAL_PARTY_CONVENTION_ACCOUNT_DISBURSEMENT", "ORG", {"F3X": "SB21B"}],
    ["INDIVIDUAL_REFUND_NP_HEADQUARTERS_ACCOUNT", "IND", {"F3X": "SB21B"}],
    ["INDIVIDUAL_REFUND_NP_CONVENTION_ACCOUNT", "IND", {"F3X": "SB21B"}],
    ["INDIVIDUAL_REFUND_NP_RECOUNT_ACCOUNT", "IND", {"F3X": "SB29"}],
    ["TRIBAL_REFUND_NP_HEADQUARTERS_ACCOUNT", "ORG", {"F3X": "SB21B"}],
    ["TRIBAL_REFUND_NP_CONVENTION_ACCOUNT", "ORG", {"F3X": "SB21B"}],
    ["TRIBAL_REFUND_NP_RECOUNT_ACCOUNT", "ORG", {"F3X": "SB29"}],
    ["OTHER_COMMITTEE_REFUND_REFUND_NP_HEADQUARTERS_ACCOUNT", "COM", {"F3X": "SB21B"}],
    ["OTHER_COMMITTEE_REFUND_REFUND_NP_CONVENTION_ACCOUNT", "COM", {"F3X": "SB21B"}],
    ["OTHER_COMMITTEE_REFUND_REFUND_NP_RECOUNT_ACCOUNT", "COM", {"F3X": "SB29"}],
    ["REFUND_INDIVIDUAL_CONTRIBUTION", "ORG", {"F3X": "SB28A"}],
    ["REFUND_INDIVIDUAL_CONTRIBUTION_VOID", "ORG", {"F3X": "SB28A"}],
    ["REFUND_PARTY_CONTRIBUTION", "COM", {"F3X": "SB28B"}],
    ["REFUND_PARTY_CONTRIBUTION_VOID", "COM", {"F3X": "SB28B"}],
    ["REFUND_PAC_CONTRIBUTION", "COM", {"F3X": "SB28C"}],
    ["REFUND_PAC_CONTRIBUTION_VOID", "COM", {"F3X": "SB28C"}],
    ["FEDERAL_ELECTION_ACTIVITY_100PCT_PAYMENT", "ORG", {"F3X": "SB30B"}],
    ["FEDERAL_ELECTION_ACTIVITY_VOID", "ORG", {"F3X": "SB30B"}],
    ["FEDERAL_ELECTION_ACTIVITY_CREDIT_CARD_PAYMENT", "ORG", {"F3X": "SB30B"}],
    ["FEDERAL_ELECTION_ACTIVITY_PAYMENT_TO_PAYROLL", "ORG", {"F3X": "SB30B"}],
    ["FEDERAL_ELECTION_ACTIVITY_CREDIT_CARD_PAYMENT_MEMO", "ORG", {"F3X": "SB30B"}],
    ["FEDERAL_ELECTION_ACTIVITY_STAFF_REIMBURSEMENT_MEMO", "ORG", {"F3X": "SB30B"}],
    ["FEDERAL_ELECTION_ACTIVITY_PAYMENT_TO_PAYROLL_MEMO", "ORG", {"F3X": "SB30B"}],
    ["IN_KIND_OUT", "IND", {"F3X": "SB21B"}],
    ["PAC_IN_KIND_OUT", "COM", {"F3X": "SB21B"}],
    ["PARTY_IN_KIND_OUT", "COM", {"F3X": "SB21B"}],
    ["IN_KIND_TRANSFER_OUT", "COM", {"F3X": "SB21B"}],
    ["IN_KIND_TRANSFER_FEA_OUT", "COM", {"F3X": "SB30B"}],
    ["CONDUIT_EARMARK_OUT_DEPOSITED", "COM", {"F3X": "SB23"}],
    ["CONDUIT_EARMARK_OUT_UNDEPOSITED", "COM", {"F3X": "SB23"}],
    ["PAC_CONDUIT_EARMARK_OUT_DEPOSITED", "COM", {"F3X": "SB23"}],
    ["PAC_CONDUIT_EARMARK_OUT_UNDEPOSITED", "COM", {"F3X": "SB23"}],
    ["LOAN_REPAYMENT_MADE", "IND", {"F3X": "SB26"}],
    ["LOAN_MADE", "COM", {"F3X": "SB27"}],
]

schedule_b_test_mappings_sampler = [
    ["OTHER_DISBURSEMENT_VOID", "COM", {"F3X": "SB29"}],
    ["OPERATING_EXPENDITURE_CREDIT_CARD_PAYMENT", "ORG", {"F3X": "SB21B"}],
    ["LOAN_MADE", "COM", {"F3X": "SB27"}],
    ["REFUND_PAC_CONTRIBUTION_VOID", "COM", {"F3X": "SB28C"}],
    ["OPERATING_EXPENDITURE_PAYMENT_TO_PAYROLL_MEMO", "IND", {"F3X": "SB21B"}],  # noqa: E501
    ["OTHER_DISBURSEMENT_PAYMENT_TO_PAYROLL_MEMO", "IND", {"F3X": "SB29"}],
]

schedule_c_test_mappings = [
    ["LOAN_RECEIVED_FROM_INDIVIDUAL", "IND", {"F3X": "SC/10"}],
    ["LOAN_RECEIVED_FROM_BANK", "ORG", {"F3X": "SC/10"}],
    ["LOAN_BY_COMMITTEE", "COM", {"F3X": "SC/9"}],
    ["C1_LOAN_AGREEMENT", "ORG", {"F3X": "SC1/10"}],
    ["C2_LOAN_GUARANTOR", "IND", {"F3X": "SC2/10"}],
]

schedule_d_test_mappings = [
    ["DEBT_OWED_TO_COMMITTEE", "COM", {"F3X": "SD9"}],
    ["DEBT_OWED_BY_COMMITTEE", "ORG", {"F3X": "SD10"}],
]

schedule_e_test_mappings = [
    ["INDEPENDENT_EXPENDITURE", "ORG", {"F3X": "SE"}],
    ["INDEPENDENT_EXPENDITURE_VOID", "ORG", {"F3X": "SE"}],
    ["INDEPENDENT_EXPENDITURE_CREDIT_CARD_PAYMENT", "ORG", {"F3X": "SE"}],
    ["INDEPENDENT_EXPENDITURE_PAYMENT_TO_PAYROLL", "ORG", {"F3X": "SE"}],
    ["INDEPENDENT_EXPENDITURE_STAFF_REIMBURSEMENT", "IND", {"F3X": "SE"}],
    ["MULTISTATE_INDEPENDENT_EXPENDITURE", "ORG", {"F3X": "SE"}],
    ["INDEPENDENT_EXPENDITURE_CREDIT_CARD_PAYMENT_MEMO", "ORG", {"F3X": "SE"}],
    ["INDEPENDENT_EXPENDITURE_STAFF_REIMBURSEMENT_MEMO", "ORG", {"F3X": "SE"}],
    ["INDEPENDENT_EXPENDITURE_PAYMENT_TO_PAYROLL_MEMO", "IND", {"F3X": "SE"}],
]

schedule_f_test_mappings = [
    ["COORDINATED_PARTY_EXPENDITURE", "ORG", {"F3X": "SF"}],
    ["COORDINATED_PARTY_EXPENDITURE_VOID", "ORG", {"F3X": "SF"}],
]


# IF THERE IS A MISMATCH, YOU MUST CHECK THE SPEC SHEET.  THIS IS NOT A SOURCE OF TRUTH


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

    def raise_for_mismatches(self, mismatches):
        if len(mismatches.keys()) == 0:
            return

        error_message = "\nTransaction Line Number mismatches found:"
        for tti in mismatches.keys():
            error_message += f"\n    {tti}"
            for report_type in mismatches[tti].keys():
                found, expected = mismatches[tti][report_type]
                error_message += (
                    f"\n        {report_type}".ljust(20)
                    + f"| {found} != {expected}"
                )

        raise AssertionError(error_message)

    def test_sch_a_line_number_annotation(self):
        mismatches = {}
        schedule_mappings = schedule_a_test_mappings
        if not RUN_ALL_TRANSACTION_TYPES:
            schedule_mappings = schedule_a_test_mappings_sampler

        for tti, entity_type, line_number_mappings in schedule_mappings:
            for report_type in line_number_mappings.keys():
                if report_type != "Unitemized":
                    report = self.get_report_for_type(report_type)
                    amount = "202.00"
                else:
                    report = self.f3x_report
                    amount = "105.00"

                new_transaction = create_schedule_a(
                    tti,
                    self.committee,
                    self.get_contact_for_entity_type(entity_type),
                    report.coverage_from_date,
                    amount,
                    report=report
                )

                if report_type == "Unitemized":
                    new_transaction.force_itemized = False
                    new_transaction.save()

                self.view.request = self.get_request(
                    params={
                        "report_id": report.id,
                    }
                )
                queryset = self.view.get_queryset()
                saved_transaction = queryset.get(id=new_transaction.id)

                if saved_transaction.form_type != line_number_mappings[report_type]:
                    tti_mismatches = mismatches.get(tti, None) or {}
                    mismatches[tti] = {
                        report_type: [
                            saved_transaction.form_type,
                            line_number_mappings[report_type]
                        ],
                        **tti_mismatches
                    }

        self.raise_for_mismatches(mismatches)

    def test_sch_b_line_number_annotation(self):
        mismatches = {}
        schedule_mappings = schedule_b_test_mappings
        if not RUN_ALL_TRANSACTION_TYPES:
            schedule_mappings = schedule_b_test_mappings_sampler

        for tti, entity_type, line_number_mappings in schedule_mappings:
            for report_type in line_number_mappings.keys():
                report = self.get_report_for_type(report_type)
                new_transaction = create_schedule_b(
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
                if saved_transaction.form_type != line_number_mappings[report_type]:
                    tti_mismatches = mismatches.get(tti, None) or {}
                    mismatches[tti] = {
                        report_type: [
                            saved_transaction.form_type,
                            line_number_mappings[report_type]
                        ],
                        **tti_mismatches
                    }

        self.raise_for_mismatches(mismatches)

    def test_sch_c_line_number_annotation(self):
        mismatches = {}
        for tti, entity_type, line_number_mappings in schedule_c_test_mappings:
            for report_type in line_number_mappings.keys():
                report = self.get_report_for_type(report_type)
                new_transaction = create_loan(
                    self.committee,
                    self.get_contact_for_entity_type(entity_type),
                    "202.00",
                    self.f3x_report.coverage_through_date,
                    "Four",
                    report=report,
                    type=tti,
                )

                self.view.request = self.get_request(
                    params={
                        "report_id": report.id,
                    }
                )
                queryset = self.view.get_queryset()
                saved_transaction = queryset.get(id=new_transaction.id)
                if saved_transaction.form_type != line_number_mappings[report_type]:
                    tti_mismatches = mismatches.get(tti, None) or {}
                    mismatches[tti] = {
                        report_type: [
                            saved_transaction.form_type,
                            line_number_mappings[report_type]
                        ],
                        **tti_mismatches
                    }

        self.raise_for_mismatches(mismatches)

    def test_sch_d_line_number_annotation(self):
        mismatches = {}
        for tti, entity_type, line_number_mappings in schedule_d_test_mappings:
            for report_type in line_number_mappings.keys():
                report = self.get_report_for_type(report_type)
                new_transaction = create_debt(
                    self.committee,
                    self.get_contact_for_entity_type(entity_type),
                    "202.00",
                    report=report,
                    type=tti,
                )

                self.view.request = self.get_request(
                    params={
                        "report_id": report.id,
                    }
                )
                queryset = self.view.get_queryset()
                saved_transaction = queryset.get(id=new_transaction.id)
                if saved_transaction.form_type != line_number_mappings[report_type]:
                    tti_mismatches = mismatches.get(tti, None) or {}
                    mismatches[tti] = {
                        report_type: [
                            saved_transaction.form_type,
                            line_number_mappings[report_type]
                        ],
                        **tti_mismatches
                    }

        self.raise_for_mismatches(mismatches)

    def test_sch_e_line_number_annotation(self):
        mismatches = {}
        for tti, entity_type, line_number_mappings in schedule_e_test_mappings:
            for report_type in line_number_mappings.keys():
                report = self.get_report_for_type(report_type)
                new_transaction = create_ie(
                    self.committee,
                    self.get_contact_for_entity_type(entity_type),
                    self.f3x_report.coverage_from_date,
                    self.f3x_report.coverage_through_date,
                    self.f3x_report.coverage_from_date,
                    "202.00",
                    "G2024",
                    self.contact_candidate,
                    report=report,
                    type=tti,
                )

                self.view.request = self.get_request(
                    params={
                        "report_id": report.id,
                    }
                )
                queryset = self.view.get_queryset()
                saved_transaction = queryset.get(id=new_transaction.id)
                if saved_transaction.form_type != line_number_mappings[report_type]:
                    tti_mismatches = mismatches.get(tti, None) or {}
                    mismatches[tti] = {
                        report_type: [
                            saved_transaction.form_type,
                            line_number_mappings[report_type]
                        ],
                        **tti_mismatches
                    }

        self.raise_for_mismatches(mismatches)

    def test_sch_f_line_number_annotation(self):
        mismatches = {}
        for tti, entity_type, line_number_mappings in schedule_f_test_mappings:
            for report_type in line_number_mappings.keys():
                report = self.get_report_for_type(report_type)
                new_transaction = create_schedule_f(
                    tti,
                    self.committee,
                    self.get_contact_for_entity_type(entity_type),
                    self.contact_candidate,
                    self.contact_committee,
                    self.contact_individual,
                    self.contact_individual,
                    report=report,
                    schedule_data={
                        "expenditure_date": report.coverage_from_date,
                        "expenditure_amount": "202",
                    }
                )

                self.view.request = self.get_request(
                    params={
                        "report_id": report.id,
                    }
                )
                queryset = self.view.get_queryset()
                saved_transaction = queryset.get(id=new_transaction.id)
                if saved_transaction.form_type != line_number_mappings[report_type]:
                    tti_mismatches = mismatches.get(tti, None) or {}
                    mismatches[tti] = {
                        report_type: [
                            saved_transaction.form_type,
                            line_number_mappings[report_type]
                        ],
                        **tti_mismatches
                    }

        self.raise_for_mismatches(mismatches)
