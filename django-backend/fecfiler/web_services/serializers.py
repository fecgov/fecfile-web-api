from rest_framework import serializers
from fecfiler.web_services.models import UploadSubmission, WebPrintSubmission
from fecfiler.reports.models import Report


class ReportIdSerializer(serializers.Serializer):
    report_id = serializers.UUIDField()

    def validate(self, data):
        request = self.context["request"]
        committee_uuid = request.session["committee_uuid"]
        report = Report.objects.filter(
            id=data["report_id"], committee_account_id=committee_uuid
        ).first()
        if not report:
            raise serializers.ValidationError(
                f"No report found with report id: {data['report_id']}"
            )
        data["report_instance"] = report
        super().validate(data)
        return data


class SubmissionRequestSerializer(ReportIdSerializer):
    password = serializers.CharField(allow_blank=False)
    backdoor_code = serializers.CharField(required=False, allow_null=True)


class UploadSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadSubmission
        fields = [
            f.name
            for f in UploadSubmission._meta.get_fields()
            if f.name not in ["dot_fec", "report"]
        ]


class WebPrintSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebPrintSubmission
        fields = [
            f.name
            for f in WebPrintSubmission._meta.get_fields()
            if f.name not in ["dot_fec", "report"]
        ]
