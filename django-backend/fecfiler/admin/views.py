from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from fecfiler.user.utils import get_user_by_email_or_id, update_user_active_state
from fecfiler.committee_accounts.committee_membership_utils import add_user_to_committee
from fecfiler.reports.utils.report_utils import reset_submitting_report
from fecfiler.web_services.utils.submission_utils import fail_open_submissions

import structlog

logger = structlog.getLogger(__name__)


class SystemAdministrationViewset(GenericViewSet):
    permission_classes=[IsAuthenticated, IsAdminUser]

    def generic_exception(self, exception):
        return Response(
            {"error": str(exception)}
        )

    @action(detail=False, methods=["post"], url_path=r"disable-user")
    def disable_user(self, request):
        email_or_id = request.data.get("user_email", request.data.get("user_id", ""))
        return self.update_user_active_state(email_or_id, False)

    @action(detail=False, methods=["post"], url_path=r"enable-user")
    def enable_user(self, request):
        email_or_id = request.data.get("user_email", request.data.get("user_id", ""))
        return self.update_user_active_state(email_or_id, True)

    def update_user_active_state(self, email_or_id: str, state: bool):
        if email_or_id == "":
            return Response(
                {"error": "user_email and user_id cannot both be missing"},
            )

        user = get_user_by_email_or_id(email_or_id)
        if user is None:
            return Response({"error": "no matching user found"})

        try:
            update_user_active_state(user, state)
        except Exception as e:
            return self.generic_exception(e)

        return Response({"success": f"user {email_or_id} updated"})

    @action(detail=False, methods=["post"], url_path=r"add-user-to-committee")
    def _add_user_to_committee(self, request):
        user_email = request.data.get("user_email")
        committee_id = request.data.get("committee_id")
        role = request.data.get("role")

        if None in [user_email, committee_id, role]:
            return Response(
                {"error": "user_email, committee_id, and role are required parameters"}
            )

        try:
            add_user_to_committee(user_email, committee_id, role)
        except Exception as e:
            return self.generic_exception(e)

        return Response(
            {"success": f"user {user_email} added to committee {committee_id}"}
        )

    @action(detail=False, methods=["post"], url_path=r"reset-submitting-report")
    def _reset_submitting_report(self, request):
        report_id = request.data.get("report_id")

        if report_id is None:
            return Response({
                "error": "report_id is a required field"
            })

        try:
            reset_submitting_report(report_id)
        except Exception as e:
            return self.generic_exception(e)

        return Response(
            {"success": f"Report {report_id} upload cleared"}
        )

    @action(detail=False, methods=["post"], url_path=r"fail-open-submissions")
    def _fail_open_submissions(self, request):
        admin_knows_what_admin_wants = request.data.get("admin_knows_what_admin_wants")
        if admin_knows_what_admin_wants is not True:
            return Response({
                "error": "admin_knows_what_admin_wants is required to be True"
            })

        try:
            fail_open_submissions()
        except Exception as e:
            return self.generic_exception(e)

        return Response(
            {"success": f"All open submissions have been closed"}
        )
