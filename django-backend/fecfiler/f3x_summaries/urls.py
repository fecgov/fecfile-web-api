from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import F3XSummaryViewSet, ReportCodeLabelViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"f3x-summaries", F3XSummaryViewSet, basename="f3x-summaries")
router.register(r"report-code-labels",ReportCodeLabelViewSet, basename="report-code-labels")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
