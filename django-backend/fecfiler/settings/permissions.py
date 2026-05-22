from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotFound


class IsE2EEnabled(BasePermission):
    def has_permission(self, request, view):
        if settings.E2E_TEST:
            return True
        raise NotFound()
