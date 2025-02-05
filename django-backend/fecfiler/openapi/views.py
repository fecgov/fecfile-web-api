from drf_spectacular.views import SpectacularSwaggerView
import secrets


class FecfileSpectacularSwaggerView(SpectacularSwaggerView):

    def get(self, request, *args, **kwargs):
        nonce = secrets.token_urlsafe(32)
        response = super().get(request, *args, **kwargs)
        response.data["nonce"] = nonce
        default_src = "default-src 'self'"
        script_src = f"script-src 'nonce-{nonce}'"
        style_src = f"style-src 'nonce-{nonce}'"
        frame_ancestors = "frame-ancestors 'none'"
        response["Content-Security-Policy"] = (
            f"{default_src}; {script_src}; {style_src}; {frame_ancestors}"
        )
        return response
