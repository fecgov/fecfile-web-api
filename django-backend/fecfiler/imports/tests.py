import csv
import io
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from fecfiler.committee_accounts.models import Membership
from fecfiler.user.models import User
from .parser import MAX_FILE_SIZE, read_mapping
from .views import ImportPreviewView


class ImportPreviewTests(SimpleTestCase):
    def make_csv(self, changes=None, header=None, trailing=None):
        report = dict.fromkeys(read_mapping("F3X"), "")
        report.update(
            {
                "form_type": "F3XA",
                "filer_committee_id_number": "C00100000",
                "committee_name": 'Example, "Committee"',
                "report_code": "M8",
                "coverage_from_date": "20260701",
                "coverage_through_date": "20260730",
                "L6b_cash_on_hand_beginning_period": "-4191.99",
            }
        )
        report.update(changes or {})
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(header or ["HDR", "FEC", "8.5", "FECfile+", "0.0.1", "", "3", ""])
        writer.writerow(report.values())
        if trailing:
            output.write(trailing)
        return output.getvalue().encode("utf-8")

    def upload(
        self, content=None, authenticated=True, committee=True, role=None, data=None
    ):
        request = APIRequestFactory().post(
            "/api/v1/imports/",
            (
                data
                if data is not None
                else {
                    "file": SimpleUploadedFile(
                        "report.csv",
                        content if content is not None else self.make_csv(),
                        content_type="text/csv",
                    )
                }
            ),
            format="multipart",
        )
        request.session = (
            {"committee_uuid": "11111111-2222-3333-4444-555555555555"}
            if committee
            else {}
        )
        user = User(pk="12345678-aaaa-bbbb-cccc-111122223333")
        if authenticated:
            force_authenticate(request, user=user)
        with patch(
            "fecfiler.committee_accounts.views.Membership.objects.filter"
        ) as memberships:
            memberships.return_value.values_list.return_value.first.return_value = (
                role or Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR
            )
            response = ImportPreviewView.as_view()(request)
            if authenticated and committee:
                memberships.assert_called_once_with(
                    user=user, committee_account_id=request.session["committee_uuid"]
                )
        return response

    def test_route_and_report_preview_without_database_access(self):
        self.assertIs(resolve("/api/v1/imports/").func.view_class, ImportPreviewView)
        response = self.upload(self.make_csv(trailing="SA11AI,transaction,data\r\n"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["report"]["committee_name"], 'Example, "Committee"'
        )
        self.assertEqual(
            response.data["report"]["L6b_cash_on_hand_beginning_period"], "-4191.99"
        )
        self.assertEqual(response.data["report"]["coverage_from_date"], "20260701")
        self.assertFalse(response.data["saved"])
        self.assertFalse(response.data["transactions_processed"])
        self.assertEqual(len(response.data["report"]), 123)

    def test_bom_and_unprocessed_transaction_rows(self):
        response = self.upload(
            b"\xef\xbb\xbf" + self.make_csv(trailing='"unterminated transaction')
        )
        self.assertEqual(response.status_code, 200)

    def test_permissions(self):
        self.assertEqual(self.upload(authenticated=False).status_code, 403)
        self.assertEqual(self.upload(committee=False).status_code, 403)
        self.assertEqual(
            self.upload(role=Membership.CommitteeRole.MANAGER).status_code, 403
        )

    def test_invalid_files(self):
        cases = [
            b"",
            b"\xff",
            b"not,a,report\n",
            b'"unterminated',
            self.make_csv(header=["HDR", "FEC", "8.4", "app", "1", "", "", ""]),
            self.make_csv(changes={"form_type": "F99"}),
            self.make_csv().splitlines()[0] + b"\nF3XA,too,short\n",
            b"x" * (MAX_FILE_SIZE + 1),
        ]
        for content in cases:
            with self.subTest(content_length=len(content)):
                self.assertEqual(self.upload(content).status_code, 400)
        self.assertEqual(self.upload(data={}).status_code, 400)
        self.assertEqual(
            self.upload(
                data={"file": SimpleUploadedFile("report.txt", self.make_csv())}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.upload(
                data={
                    "file": [
                        SimpleUploadedFile("one.csv", self.make_csv()),
                        SimpleUploadedFile("two.csv", self.make_csv()),
                    ]
                }
            ).status_code,
            400,
        )
