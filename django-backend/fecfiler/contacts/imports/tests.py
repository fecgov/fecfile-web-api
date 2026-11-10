import csv
import io
import tempfile
from datetime import timedelta
from django.core.management import call_command
from django.utils import timezone
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import resolve
from import_export_extensions.models import ImportJob
from rest_framework.test import APIRequestFactory, force_authenticate

from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.contacts.models import Contact
from fecfiler.user.models import User
from .format import CONTACT_COLUMNS, ContactsCSV
from .resource import ContactImportResource
from .views import ContactImportViewSet


@override_settings(FLAG__ENABLE_IMPORT=True)
class ContactImportTests(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(pk="12345678-aaaa-bbbb-cccc-111122223333")
        self.committee = CommitteeAccount.objects.get(committee_id="C01234567")
        self.storage = tempfile.TemporaryDirectory()
        self.addCleanup(self.storage.cleanup)
        settings_override = override_settings(MEDIA_ROOT=self.storage.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self.factory = APIRequestFactory()
        self.resource = ContactImportResource(
            committee_id=str(self.committee.pk), user_id=str(self.user.pk)
        )

    def row(self, contact_type="IND", **kwargs):
        data = dict(
            type=contact_type,
            street_1="123 Example St",
            city="Annapolis",
            state="MD",
            zip="01234",
            country="USA",
        )
        if contact_type in ("IND", "CAN"):
            data.update(first_name="Alex", last_name="Example")
        if contact_type in ("COM", "ORG"):
            data["name"] = "Example Organization"
        if contact_type == "COM":
            data["committee_id"] = "C00123456"
        if contact_type == "CAN":
            data.update(
                candidate_id="H0MD12345",
                candidate_office="H",
                candidate_state="MD",
                candidate_district="01",
            )
        data.update(kwargs)
        return data

    def csv(self, rows):
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=CONTACT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def dataset(self, rows):
        return ContactsCSV().create_dataset(self.csv(rows))

    def request(self, action, data=None, pk=None, committee=None, authenticated=True):
        url = "/api/v1/contacts/imports/" + (
            "start/"
            if action == "start_import_action"
            else f"{pk}/" + ("" if action == "retrieve" else f"{action}/")
        )
        request = (
            self.factory.get(url)
            if action == "retrieve"
            else self.factory.post(url, data or {}, format="multipart")
        )
        request.session = {"committee_uuid": str((committee or self.committee).pk)}
        if authenticated:
            force_authenticate(request, self.user)
        view = ContactImportViewSet.as_view(
            {"get" if action == "retrieve" else "post": action}
        )
        with self.captureOnCommitCallbacks(execute=False):
            return view(request, **({"pk": pk} if pk else {}))

    def start(self, rows, **data):
        return self.request(
            "start_import_action",
            {
                "file": SimpleUploadedFile(
                    "contacts.csv", self.csv(rows).encode(), content_type="text/csv"
                ),
                **data,
            },
        )

    def test_all_types_create_only_and_preserve_strings(self):
        result = self.resource.import_data(
            self.dataset([self.row(t) for t in ("IND", "ORG", "COM", "CAN")]),
            dry_run=True,
        )
        self.assertFalse(result.has_errors())
        self.assertFalse(result.has_validation_errors())
        self.assertEqual(Contact.objects.count(), 0)
        result = self.resource.import_data(
            self.dataset([self.row(t) for t in ("IND", "ORG", "COM", "CAN")])
        )
        self.assertFalse(result.has_errors())
        self.assertEqual(Contact.objects.count(), 4)
        self.assertEqual(Contact.objects.get(type="CAN").candidate_district, "01")
        self.assertEqual(Contact.objects.get(type="IND").zip, "01234")
        self.assertEqual(
            set(Contact.objects.values_list("committee_account_id", flat=True)),
            {self.committee.pk},
        )
        duplicate = self.resource.import_data(
            self.dataset([self.row("COM"), self.row("CAN")])
        )
        self.assertFalse(duplicate.has_validation_errors())
        self.assertEqual(Contact.objects.count(), 6)

    def test_invalid_row_rolls_back_every_contact_even_with_unsafe_options(self):
        for invalid in (
            self.row(first_name=""),
            self.row("CAN", candidate_district=""),
            self.row("ORG", name=""),
            self.row("COM", committee_id="bad"),
            self.row("BAD"),
            self.row("IND", name="Wrong field"),
            self.row(zip=""),
        ):
            with self.subTest(invalid=invalid):
                result = self.resource.import_data(
                    self.dataset([self.row(), invalid]),
                    force_import=True,
                    use_transactions=False,
                )
                self.assertTrue(result.has_validation_errors())
                self.assertEqual(Contact.objects.count(), 0)

    def test_save_failure_rolls_back_previous_rows(self):
        original = Contact.save

        def save(contact, *args, **kwargs):
            if contact.first_name == "Fail":
                raise IntegrityError("Simulated write failure")
            return original(contact, *args, **kwargs)

        with patch.object(Contact, "save", save):
            result = self.resource.import_data(
                self.dataset([self.row(), self.row(first_name="Fail")])
            )
        self.assertTrue(result.has_errors())
        self.assertEqual(Contact.objects.count(), 0)

    def test_job_preview_confirm_and_no_double_confirmation(self):
        response = self.start([self.row(), self.row("CAN")])
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIs(
            resolve("/api/v1/contacts/imports/start/").func.cls, ContactImportViewSet
        )
        job = ImportJob.objects.get(pk=response.data["id"])
        self.assertEqual(job.resource_kwargs["committee_id"], str(self.committee.pk))
        job.parse_data()
        job.refresh_from_db()
        self.assertEqual(job.import_status, "PARSED", job.error_message)
        self.assertEqual(Contact.objects.count(), 0)
        detail = self.request("retrieve", pk=job.pk)
        self.assertEqual(detail.data["total_rows"], 2)
        self.assertEqual(len(detail.data["preview"]), 2)
        self.assertNotIn("data_file", detail.data)
        self.assertEqual(self.request("confirm", pk=job.pk).status_code, 200)
        self.assertEqual(self.request("confirm", pk=job.pk).status_code, 400)
        job.refresh_from_db()
        job.import_data()
        self.assertEqual(job.import_status, "IMPORTED", job.error_message)
        self.assertEqual(Contact.objects.count(), 2)

    def test_invalid_job_cannot_be_confirmed_and_reports_csv_row(self):
        response = self.start([self.row(), self.row("CAN", candidate_id="bad")])
        job = ImportJob.objects.get(pk=response.data["id"])
        job.parse_data()
        job.refresh_from_db()
        self.assertEqual(job.import_status, "INPUT_ERROR", job.error_message)
        detail = self.request("retrieve", pk=job.pk)
        self.assertEqual(detail.data["errors"][0]["row"], 3)
        self.assertIn("candidate_id", detail.data["errors"][0]["fields"])
        self.assertEqual(self.request("confirm", pk=job.pk).status_code, 400)
        self.assertEqual(Contact.objects.count(), 0)

    def test_access_scope_and_recheck_creator_permissions(self):
        self.assertEqual(
            self.request("start_import_action", authenticated=False).status_code, 403
        )
        response = self.start([self.row()])
        job = ImportJob.objects.get(pk=response.data["id"])
        other = CommitteeAccount.objects.create(committee_id="C00999999")
        Membership.objects.create(
            user=self.user,
            committee_account=other,
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
        )
        self.assertEqual(
            self.request("retrieve", pk=job.pk, committee=other).status_code, 404
        )
        self.assertEqual(
            self.request("confirm", pk=job.pk, committee=other).status_code, 404
        )
        Membership.objects.filter(
            user=self.user, committee_account=self.committee
        ).update(role=Membership.CommitteeRole.MANAGER)
        self.assertEqual(self.request("retrieve", pk=job.pk).status_code, 403)
        job.parse_data()
        self.assertEqual(job.import_status, "PARSE_ERROR")
        self.assertEqual(Contact.objects.count(), 0)

    def test_reject_partial_imports_and_internal_columns(self):
        self.assertEqual(self.start([self.row()], force_import="true").status_code, 400)
        self.assertEqual(
            self.start([self.row()], skip_parse_step="true").status_code, 400
        )
        for csv_text in (
            "type,type\nIND,IND",
            "id,type\n123,IND",
            "type,street_1,city,state,country\nIND,Street,City,MD,USA,extra",
            'type,street_1,city,state,country\n"unterminated',
        ):
            with self.subTest(csv_text=csv_text), self.assertRaises(ValueError):
                ContactsCSV().create_dataset(csv_text)

    def test_revoked_creator_after_preview_blocks_final_import(self):
        response = self.start([self.row()])
        job = ImportJob.objects.get(pk=response.data["id"])
        job.parse_data()
        self.assertEqual(job.import_status, "PARSED")
        self.request("confirm", pk=job.pk)
        Membership.objects.filter(
            user=self.user, committee_account=self.committee
        ).update(role=Membership.CommitteeRole.MANAGER)
        job.refresh_from_db()
        job.import_data()
        self.assertEqual(job.import_status, "IMPORT_ERROR")
        self.assertEqual(Contact.objects.count(), 0)

    def test_file_limits_and_empty_files(self):
        from .format import MAX_FILE_SIZE

        for file in (
            SimpleUploadedFile("empty.csv", b""),
            SimpleUploadedFile("large.csv", b"x" * (MAX_FILE_SIZE + 1)),
            SimpleUploadedFile("wrong.txt", b"text"),
        ):
            self.assertEqual(
                self.request("start_import_action", {"file": file}).status_code, 400
            )

    def test_cleanup_is_opt_in_and_removes_only_old_finished_jobs(self):
        response = self.start([self.row()])
        job = ImportJob.objects.get(pk=response.data["id"])
        job.parse_data()
        filename = job.data_file.name
        storage = job.data_file.storage
        ImportJob.objects.filter(pk=job.pk).update(
            modified=timezone.now() - timedelta(days=8)
        )
        call_command("cleanup_contact_imports", stdout=io.StringIO())
        self.assertTrue(ImportJob.objects.filter(pk=job.pk).exists())
        call_command("cleanup_contact_imports", delete=True, stdout=io.StringIO())
        self.assertFalse(ImportJob.objects.filter(pk=job.pk).exists())
        self.assertFalse(storage.exists(filename))
