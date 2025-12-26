import importlib
import sys
import types

from django.test import SimpleTestCase

import fecfiler.settings as fec_settings


class UrlsTest(SimpleTestCase):
    def test_urls_include_silk_when_enabled(self):
        original_enabled = fec_settings.FECFILE_SILK_ENABLED
        original_static_url = getattr(fec_settings, "STATIC_URL", None)
        original_static_root = getattr(fec_settings, "STATIC_ROOT", None)
        original_silk = sys.modules.get("silk")
        original_silk_urls = sys.modules.get("silk.urls")
        try:
            fec_settings.FECFILE_SILK_ENABLED = True
            fec_settings.STATIC_URL = "/static/"
            fec_settings.STATIC_ROOT = "/tmp/static"

            silk_module = types.ModuleType("silk")
            silk_urls = types.ModuleType("silk.urls")
            silk_urls.app_name = "silk"
            silk_urls.urlpatterns = []
            sys.modules["silk"] = silk_module
            sys.modules["silk.urls"] = silk_urls

            import fecfiler.urls as urls

            urls = importlib.reload(urls)
            self.assertTrue(
                any("silk" in str(pattern.pattern) for pattern in urls.urlpatterns)
            )
        finally:
            fec_settings.FECFILE_SILK_ENABLED = original_enabled
            if original_static_url is None:
                if hasattr(fec_settings, "STATIC_URL"):
                    delattr(fec_settings, "STATIC_URL")
            else:
                fec_settings.STATIC_URL = original_static_url
            if original_static_root is None:
                if hasattr(fec_settings, "STATIC_ROOT"):
                    delattr(fec_settings, "STATIC_ROOT")
            else:
                fec_settings.STATIC_ROOT = original_static_root

            if original_silk is None:
                sys.modules.pop("silk", None)
            else:
                sys.modules["silk"] = original_silk
            if original_silk_urls is None:
                sys.modules.pop("silk.urls", None)
            else:
                sys.modules["silk.urls"] = original_silk_urls
            import fecfiler.urls as urls

            importlib.reload(urls)
