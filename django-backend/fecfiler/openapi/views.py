from drf_spectacular.views import SpectacularSwaggerView
from drf_spectacular.utils import extend_schema, extend_schema_view
import secrets


@extend_schema_view(get=extend_schema(exclude=True))
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
