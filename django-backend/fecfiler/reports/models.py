from typing import Any
from django.db import models
from fecfiler.reports.managers import ReportManager
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.reports.f3x_report.models import F3XReport
import uuid
import logging


logger = logging.getLogger(__name__)


class Report(SoftDeleteModel, CommitteeOwnedModel):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    _form_type = models.TextField(null=True, blank=True)

    @property
    def form_type(self):
        return self._form_type

    @form_type.setter
    def form_type(self, value):
        self._form_type = value

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    upload_submission = models.ForeignKey(
        "web_services.UploadSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    webprint_submission = models.ForeignKey(
        "web_services.WebPrintSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    f3x_report = models.ForeignKey(
        F3XReport, on_delete=models.CASCADE, null=True, blank=True
    )

    objects = ReportManager()

    """
    def __getattribute__(self, name):
        if hasattr(self, name):
            return self.__dict__[name]

        report_instances = [
            self.f3x_report,
        ]
        for report in report_instances:
            if report and hasattr(report, name):
                return report.__getattribute__(name)

        raise AttributeError
    """

    def get_report_name(self):
        report_map = {
            "f3x_report": Report.F3X,
        }
        for report_key in report_map:
            if getattr(self, report_key, None):
                return report_map[report_key]
        return None

    def get_schedule(self):
        for report_key in [
            "f3x_report",
        ]:
            if getattr(self, report_key, None):
                return getattr(self, report_key)
