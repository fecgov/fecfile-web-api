from rest_framework import serializers
from fecfiler.f3x_summaries.models import F3XSummary


class ReportIdSerializer(serializers.Serializer):
    report_id = serializers.IntegerField()

    def validate(self, data):
        request = self.context["request"]
        committee_id = request.user.cmtee_id
        f3x_summary_result = F3XSummary.objects.filter(
            id=data["report_id"], committee_account__committee_id=committee_id
        )
        if not f3x_summary_result.exists():
            raise serializers.ValidationError(
                f"No f3x summary found with report id: {data['report_id']}"
            )
        return data
