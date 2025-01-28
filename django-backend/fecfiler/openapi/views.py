from drf_spectacular.views import SpectacularSwaggerView
import secrets


class FecfileSpectacularSwaggerView(SpectacularSwaggerView):

    def get(self, request, *args, **kwargs):
        nonce = secrets.token_urlsafe(32)
        response = super().get(request, *args, **kwargs)
        response.data["nonce"] = nonce
        response["Content-Security-Policy"] = (
            f"default-src 'self'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'"
        )
        return response
