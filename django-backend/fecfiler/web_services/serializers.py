from rest_framework import serializers
from fecfiler.web_services.models import UploadSubmission, WebPrintSubmission
from fecfiler.reports.f3x_report.models import F3XReport


class ReportIdSerializer(serializers.Serializer):
    report_id = serializers.UUIDField()

    def validate(self, data):
        request = self.context["request"]
        committee_id = request.user.cmtee_id
        f3x_summary_result = F3XReport.objects.filter(
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
