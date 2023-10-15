from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .form_3x.views import Form3XViewSet
from .form_24.views import Form24ViewSet
from .views import ReportViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"form-3x", Form3XViewSet, basename="form-3x")
router.register(r"form-24", Form24ViewSet, basename="form-24")
router.register(r"form-99", Form24ViewSet, basename="form-99")
router.register(r"", ReportViewSet, basename="reports")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("reports/", include(router.urls))]
