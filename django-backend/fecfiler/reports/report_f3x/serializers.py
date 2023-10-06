from .models import ReportF3X
from django.db.models import Q
from rest_framework.serializers import EmailField, CharField, ValidationError
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.web_services.serializers import (
    UploadSubmissionSerializer,
    WebPrintSubmissionSerializer,
)
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
import logging

COVERAGE_DATE_REPORT_CODE_COLLISION = ValidationError(
    {"report_code": ["Collision with existing report_code and year"]}
)

logger = logging.getLogger(__name__)


class ReportF3XSerializer(CommitteeOwnedSerializer, FecSchemaValidatorSerializerMixin):
    schema_name = "F3X"
    confirmation_email_1 = EmailField(
        max_length=44,
        min_length=None,
        allow_blank=True,
        allow_null=True,
        required=False,
    )
    confirmation_email_2 = EmailField(
        max_length=44,
        min_length=None,
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    def save(self, **kwargs):
        """Raise a ValidationError if an F3X with the same report code
        exists for the same year
        """
        request = self.context["request"]
        committee_id = request.user.cmtee_id
        number_of_collisions = ReportF3X.objects.filter(
            ~Q(id=(self.instance or ReportF3X()).id),
            committee_account__committee_id=committee_id,
            coverage_from_date__year=self.validated_data["coverage_from_date"].year,
            report_code=self.validated_data["report_code"],
        ).count()
        if number_of_collisions == 0:
            return super(ReportF3XSerializer, self).save(**kwargs)
        else:
            raise COVERAGE_DATE_REPORT_CODE_COLLISION

    def validate(self, data):
        self.context["fields_to_ignore"] = self.context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    class Meta:
        model = ReportF3X
        fields = [
            f.name
            for f in ReportF3X._meta.get_fields()
            if f.name
            not in [
                "deleted",
                "schatransaction",
                "scheduleatransaction",
                "schedulebtransaction",
                "transaction",
                "dotfec",
                "memotext",
                "uploadsubmission",
                "webprintsubmission",
            ]
        ] + ["report_status", "report_code_label", "fields_to_validate"]
        read_only_fields = ["id", "deleted", "created", "updated"]
