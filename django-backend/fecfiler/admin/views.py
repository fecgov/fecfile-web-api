from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from fecfiler.user.utils import get_user_by_email_or_id, update_user_active_state
import structlog

logger = structlog.getLogger(__name__)


class SystemAdministrationViewset(GenericViewSet):
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

        update_user_active_state(user, state)
        return Response({"success": f"user {email_or_id} updated"})


