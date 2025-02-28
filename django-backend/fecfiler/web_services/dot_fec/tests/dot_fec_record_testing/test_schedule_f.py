from decimal import Decimal
from django.test import TestCase
from fecfiler.transactions.models import Transaction
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_transactions
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_schedule_f
from fecfiler.contacts.tests.utils import (
    create_test_individual_contact,
    create_test_committee_contact,
    create_test_candidate_contact,
    create_test_organization_contact,
)
from datetime import datetime
from fecfiler.web_services.models import UploadSubmission
import structlog

logger = structlog.get_logger(__name__)


class DotFECScheduleFTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        coverage_from = datetime.strptime("2024-01-01", "%Y-%m-%d")
        coverage_through = datetime.strptime("2024-02-01", "%Y-%m-%d")
        self.f3x = create_form3x(
            self.committee,
            coverage_from,
            coverage_through,
        )

        upload_submission = UploadSubmission.objects.initiate_submission(self.f3x.id)
        self.f3x.upload_submission = upload_submission
        self.f3x.save()

        self.contact_2 = create_test_candidate_contact(
            "last name",
            "first name",
            self.committee.id,
            "H8MA03131",
            "S",
            "AK",
            "01",
            {
                "street_1": "Steet 1",
                "street_2": "Steet 2",
                "city": "City",
                "state": "State",
                "zip": "Zip",
                "middle_name": "middle name",
                "prefix": "Sir",
                "suffix": "jr",
            },
        )

        self.contact_3 = create_test_committee_contact(
            "Test Committee",
            self.committee.id,
            self.committee.id,
            {
                "street_1": "Steet 1",
                "street_2": "Steet 2",
                "city": "City",
                "state": "State",
                "zip": "Zip",
            },
        )

    def test_ind_form(self):
        contact_1 = create_test_individual_contact(
            "last name",
            "first name",
            self.committee.id,
            {
                "street_1": "Steet 1",
                "street_2": "Steet 2",
                "city": "City",
                "state": "State",
                "zip": "Zip",
            },
        )

        transaction = create_schedule_f(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            contact_1,
            self.contact_2,
            self.contact_3,
            schedule_data={
                "expenditure_date": "2024-01-04",
                "expenditure_amount": "250.00",
                "filer_designated_to_make_coordianted_expenditures": True,
                "designating_committee_account": self.committee,
                "designating_committee_name": "DESIGNATING NAME",
                "aggregate_general_elec_expended": Decimal(500.00),
                "expenditure_purpose_descrip": "TEST DESCRIP",
                "category_code": "CODE",
                "memo_text_description": "TEST MEMO DESCRIP",
            },
            memo_code=True,
            report=self.f3x,
        )
        transaction.itemized = True
        transaction.save()
        self.run_test(transaction)

    def test_org_form(self):
        contact_1 = create_test_organization_contact(
            "test org",
            self.committee.id,
            {
                "street_1": "Steet 1",
                "street_2": "Steet 2",
                "city": "City",
                "state": "State",
                "zip": "Zip",
            },
        )

        transaction = create_schedule_f(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            contact_1,
            self.contact_2,
            self.contact_3,
            schedule_data={
                "expenditure_date": "2024-01-04",
                "expenditure_amount": "250.00",
                "filer_designated_to_make_coordianted_expenditures": True,
                "designating_committee_account": self.committee,
                "designating_committee_name": "DESIGNATING NAME",
                "aggregate_general_elec_expended": Decimal(500.00),
                "expenditure_purpose_descrip": "TEST DESCRIP",
                "category_code": "CODE",
                "memo_text_description": "TEST MEMO DESCRIP",
            },
            memo_code=False,
            report=self.f3x,
        )
        transaction.itemized = True
        transaction.save()
        self.run_test(transaction)

    def run_test(self, transaction: Transaction):
        transactions = compose_transactions(self.f3x.id)
        serialized_transaction = serialize_instance("SchF", transactions[0])
        self.split_row = serialized_transaction.split(FS_STR)

        self.assertEqual(
            transaction.contact_1.first_name, transaction.contact_1.first_name
        )
        self.assertEqual(self.split_row[field_to_num["form_type"]], "SF")
        self.assertEqual(
            self.split_row[field_to_num["filer_committee_id_number"]],
            self.committee.committee_id,
        )
        self.assertEqual(
            self.split_row[field_to_num["transaction_id_number"]],
            transaction.transaction_id,
        )
        self.assertEqual(
            self.split_row[field_to_num["back_reference_tran_id_number"]],
            "",
        )
        self.assertEqual(self.split_row[field_to_num["back_reference_sched_name"]], "")

        self.assertEqual(
            self.split_row[
                field_to_num["filer_designated_to_make_coordianted_expenditures"]
            ],
            "Y",
        )
        self.assertEqual(
            self.split_row[field_to_num["designating_committee_id_number"]],
            self.committee.committee_id,
        )
        self.assertEqual(
            self.split_row[field_to_num["designating_committee_name"]],
            transaction.schedule_f.designating_committee_name,
        )

        self.assertEqual(
            self.split_row[field_to_num["subordinate_committee_id_number"]],
            str(self.contact_3.committee_id),
        )
        self.assertEqual(
            self.split_row[field_to_num["subordinate_committee_name"]],
            self.contact_3.name,
        )
        self.assertEqual(
            self.split_row[field_to_num["subordinate_street_1"]],
            self.contact_3.street_1,
        )
        self.assertEqual(
            self.split_row[field_to_num["subordinate_street_2"]],
            self.contact_3.street_2,
        )
        self.assertEqual(
            self.split_row[field_to_num["subordinate_city"]], self.contact_3.city
        )
        self.assertEqual(
            self.split_row[field_to_num["subordinate_state"]], self.contact_3.state
        )
        self.assertEqual(
            self.split_row[field_to_num["subordinate_zip"]], self.contact_3.zip
        )

        self.assertEqual(
            self.split_row[field_to_num["entity_type"]], transaction.contact_1.type
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_organization_name"]],
            transaction.contact_1.name if transaction.contact_1.type == "ORG" else "",
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_last_name"]],
            (
                transaction.contact_1.last_name
                if transaction.contact_1.type == "IND"
                else ""
            ),
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_first_name"]],
            (
                transaction.contact_1.first_name
                if transaction.contact_1.type == "IND"
                else ""
            ),
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_middle_name"]],
            transaction.contact_1.middle_name or "",
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_prefix"]],
            transaction.contact_1.prefix or "",
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_suffix"]],
            transaction.contact_1.suffix or "",
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_street_1"]], transaction.contact_1.street_1
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_street_2"]], transaction.contact_1.street_2
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_city"]], transaction.contact_1.city
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_state"]], transaction.contact_1.state
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_zip"]], transaction.contact_1.zip
        )

        self.assertEqual(
            self.split_row[field_to_num["expenditure_date"]],
            transaction.schedule_f.expenditure_date.replace("-", ""),
        )
        self.assertEqual(
            self.split_row[field_to_num["expenditure_amount"]],
            transaction.schedule_f.expenditure_amount,
        )
        self.assertEqual(
            Decimal(self.split_row[field_to_num["aggregate_general_elec_expended"]]),
            transaction.schedule_f.aggregate_general_elec_expended,
        )
        self.assertEqual(
            self.split_row[field_to_num["expenditure_purpose_descrip"]],
            transaction.schedule_f.expenditure_purpose_descrip,
        )
        self.assertEqual(
            self.split_row[field_to_num["category_code"]],
            transaction.schedule_f.category_code,
        )

        self.assertEqual(
            self.split_row[field_to_num["payee_committee_id_number"]],
            str(self.contact_2.committee_account.id),
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_candidate_id_number"]],
            self.contact_2.candidate_id,
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_candidate_last_name"]],
            self.contact_2.last_name,
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_candidate_first_name"]],
            self.contact_2.first_name,
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_candidate_middle_name"]],
            self.contact_2.middle_name or "",
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_candidate_prefix"]],
            self.contact_2.prefix or "",
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_candidate_suffix"]],
            self.contact_2.suffix or "",
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_candidate_office"]],
            self.contact_2.candidate_office,
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_candidate_state"]],
            self.contact_2.candidate_state,
        )
        self.assertEqual(
            self.split_row[field_to_num["payee_candidate_district"]],
            self.contact_2.candidate_district,
        )

        self.assertEqual(
            self.split_row[field_to_num["memo_code"]],
            "X" if transaction.memo_code else "",
        )
        self.assertEqual(
            self.split_row[field_to_num["memo_text_description"]],
            transaction.schedule_f.memo_text_description or "",
        )


field_to_num = {
    "form_type": 0,
    "filer_committee_id_number": 1,
    "transaction_id_number": 2,
    "back_reference_tran_id_number": 3,
    "back_reference_sched_name": 4,
    "filer_designated_to_make_coordianted_expenditures": 5,
    "designating_committee_id_number": 6,
    "designating_committee_name": 7,
    "subordinate_committee_id_number": 8,
    "subordinate_committee_name": 9,
    "subordinate_street_1": 10,
    "subordinate_street_2": 11,
    "subordinate_city": 12,
    "subordinate_state": 13,
    "subordinate_zip": 14,
    "entity_type": 15,
    "payee_organization_name": 16,
    "payee_last_name": 17,
    "payee_first_name": 18,
    "payee_middle_name": 19,
    "payee_prefix": 20,
    "payee_suffix": 21,
    "payee_street_1": 22,
    "payee_street_2": 23,
    "payee_city": 24,
    "payee_state": 25,
    "payee_zip": 26,
    "expenditure_date": 27,
    "expenditure_amount": 28,
    "aggregate_general_elec_expended": 29,
    "expenditure_purpose_descrip": 30,
    "category_code": 31,
    "payee_committee_id_number": 32,
    "payee_candidate_id_number": 33,
    "payee_candidate_last_name": 34,
    "payee_candidate_first_name": 35,
    "payee_candidate_middle_name": 36,
    "payee_candidate_prefix": 37,
    "payee_candidate_suffix": 38,
    "payee_candidate_office": 39,
    "payee_candidate_state": 40,
    "payee_candidate_district": 41,
    "memo_code": 42,
    "memo_text_description": 43,
}
