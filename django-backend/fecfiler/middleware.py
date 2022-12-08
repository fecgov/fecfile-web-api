from fecfiler.settings.base import URLS_TO_EXCLUDE_FROM_AUTH_CHECK
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class LoginRequiredMiddleware(MiddlewareMixin):
    """Checks if the user is authenticated with fecfile and returns an
    HTTP 401 Unauthorized error if not."""

    def process_request(self, request):
        if (not request.user.is_authenticated
                and request.path.startswith("/api/v1")
                and request.path not in URLS_TO_EXCLUDE_FROM_AUTH_CHECK):
            return HttpResponse(status=401)
