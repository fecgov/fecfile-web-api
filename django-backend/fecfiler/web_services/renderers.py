from rest_framework import renderers


class DotFECRenderer(renderers.BaseRenderer):
    """DRF Renderer for returning .FEC files from an endpoint"""

    media_type = "application/octet-stream"
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data
