from django.urls import path, include
from fecfiler.reports.form_99.views import Form99ViewSet
from fecfiler.routers import register_router
from .form_3.views import Form3ViewSet
from .form_3x.views import Form3XViewSet
from .form_24.views import Form24ViewSet
from .form_1m.views import Form1MViewSet
from .views import ReportViewSet

router = register_router()
router.register(r"form-3", Form3ViewSet, basename="form-3")
router.register(r"form-3x", Form3XViewSet, basename="form-3x")
router.register(r"form-24", Form24ViewSet, basename="form-24")
router.register(r"form-99", Form99ViewSet, basename="form-99")
router.register(r"form-1m", Form1MViewSet, basename="form-1m")
router.register(r"", ReportViewSet, basename="reports")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("reports/", include(router.urls))]
