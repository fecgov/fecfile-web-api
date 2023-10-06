from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .report_f3x.views import ReportF3XViewSet
from .views import ReportViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"report-f3x", ReportF3XViewSet, basename="report-f3x")
router.register(r"", ReportViewSet, basename="reports")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("reports/", include(router.urls))]
