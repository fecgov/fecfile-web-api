from django.conf import settings
from django.utils.http import parse_http_date_safe

from fecfiler.settings import (
    FFAPI_TIMEOUT_COOKIE_NAME,
    FFAPI_COOKIE_DOMAIN,
)


class TimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        session_cookie = response.cookies.get(settings.SESSION_COOKIE_NAME)
        if session_cookie:
            response.set_cookie(
                FFAPI_TIMEOUT_COOKIE_NAME,
                parse_http_date_safe(session_cookie.get("expires")),
                max_age=session_cookie.get("max-age"),
                expires=session_cookie.get("expires"),
                domain=FFAPI_COOKIE_DOMAIN,
                secure=True,
                samesite=settings.SESSION_COOKIE_SAMESITE
            )

        return response
