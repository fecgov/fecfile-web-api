from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet
from fecfiler.reports.f3x_report.views import F3XReportViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"f3x-reports", F3XReportViewSet, basename="f3x-reports")
router.register(r"", ReportViewSet, basename="reports")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("reports/", include(router.urls))]
