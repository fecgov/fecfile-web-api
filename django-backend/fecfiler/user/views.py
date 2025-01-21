from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from .serializers import CurrentUserSerializer, session_security_consented_key
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


class UserViewSet(
    GenericViewSet,
):
    @action(detail=False, methods=["get"])
    def get_current(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["put"])
    def update_current(self, request):
        additional_data = {}
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        consent_for_one_year = serializer.validated_data.pop("consent_for_one_year", None)
        if consent_for_one_year:
            additional_data["security_consent_exp_date"] = date.today() + timedelta(
                days=365
            )
        else:
            request.session[session_security_consented_key] = True
        serializer.save(**additional_data)
        return Response(serializer.data)

    serializer_class = CurrentUserSerializer
    pagination_class = None
