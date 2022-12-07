from rest_framework import serializers
from fecfiler.web_services.models import UploadSubmission, WebPrintSubmission
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.authentication.authenticate_login import get_logged_in_user


class ReportIdSerializer(serializers.Serializer):
    report_id = serializers.UUIDField()

    def validate(self, data):
        request = self.context["request"]
        user = get_logged_in_user(request)
        committee_id = user.cmtee_id
        f3x_summary_result = F3XSummary.objects.filter(
            id=data["report_id"], committee_account__committee_id=committee_id
        )
        if not f3x_summary_result.exists():
            raise serializers.ValidationError(
                f"No f3x summary found with report id: {data['report_id']}"
            )
        return super().validate(data)


class SubmissionRequestSerializer(ReportIdSerializer):
    password = serializers.CharField(allow_blank=False)


class UploadSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadSubmission
        fields = [
            f.name
            for f in UploadSubmission._meta.get_fields()
            if f.name not in ["dot_fec", "f3xsummary"]
        ]


class WebPrintSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebPrintSubmission
        fields = [
            f.name
            for f in WebPrintSubmission._meta.get_fields()
            if f.name not in ["dot_fec", "f3xsummary"]
        ]
