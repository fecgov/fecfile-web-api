from django.conf.urls import include
from django.urls import re_path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

BASE_V1_URL = r"^api/v1/"


@api_view(["GET"])
def test_celery(_request):
    from fecfiler.celery import debug_task

    debug_task.delay()
    return Response(status=200)


@api_view(["GET"])
@permission_classes([])
def get_api_status(_request):
    return Response(status=200)


urlpatterns = [
    re_path(BASE_V1_URL, include("fecfiler.committee_accounts.urls")),
    re_path(BASE_V1_URL, include("fecfiler.contacts.urls")),
    re_path(BASE_V1_URL, include("fecfiler.reports.urls")),
    re_path(BASE_V1_URL, include("fecfiler.memo_text.urls")),
    re_path(BASE_V1_URL, include("fecfiler.transactions.urls")),
    re_path(BASE_V1_URL, include("fecfiler.authentication.urls")),
    re_path(BASE_V1_URL, include("fecfiler.web_services.urls")),
    re_path(BASE_V1_URL, include("fecfiler.openfec.urls")),
    re_path(BASE_V1_URL, include("fecfiler.user.urls")),
    re_path(BASE_V1_URL, include("fecfiler.feedback.urls")),
    re_path(r"^oidc/", include("mozilla_django_oidc.urls")),
    re_path(r"^celery-test/", test_celery),
    re_path(r"^status/", get_api_status)
]
