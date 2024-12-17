from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
import datetime
import logging

logger = logging.getLogger(__name__)

session_security_consented_key = "session_security_consented"


class UserViewSet(ModelViewSet):

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        augmented_response = {
            "security_consented": (
                datetime.datetime.now() <= request.user.security_consent_exp_date
                or request.session[session_security_consented_key]
            )
        }
        augmented_response.update(serializer.data)
        return Response(augmented_response)

    def update(self, request, *args, **kwargs):
        add_session_consent = False
        consent_for_one_year = request.data.get("consent_for_one_year", None)
        if consent_for_one_year:
            request.data["security_consent_exp_date"] = (
                datetime.datetime.now() + datetime.timedelta(days=365)
            )
        else:
            add_session_consent = True
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if add_session_consent:
            request.session[session_security_consented_key] = True
        return Response(serializer.data)
