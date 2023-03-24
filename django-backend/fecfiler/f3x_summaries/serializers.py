from .models import F3XSummary
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


class F3XSummarySerializer(CommitteeOwnedSerializer, FecSchemaValidatorSerializerMixin):
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
    upload_submission = UploadSubmissionSerializer(
        read_only=True,
    )
    webprint_submission = WebPrintSubmissionSerializer(
        read_only=True,
    )
    report_status = CharField(
        read_only=True,
    )
    report_code_label = CharField(
        read_only=True,
    )

    def save(self, **kwargs):
        """Raise a ValidationError if an F3X with the same report code
        exists for the same year
        """
        request = self.context["request"]
        committee_id = request.user.cmtee_id
        number_of_collisions = F3XSummary.objects.filter(
            ~Q(id=(self.instance or F3XSummary()).id),
            committee_account__committee_id=committee_id,
            coverage_from_date__year=self.validated_data["coverage_from_date"].year,
            report_code=self.validated_data["report_code"],
        ).count()
        if number_of_collisions is 0:
            return super(F3XSummarySerializer, self).save(**kwargs)
        else:
            raise COVERAGE_DATE_REPORT_CODE_COLLISION

    class Meta:
        model = F3XSummary
        fields = [
            f.name
            for f in F3XSummary._meta.get_fields()
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
        ] + ["report_status", "report_code_label"]
        read_only_fields = ["id", "deleted", "created", "updated"]
