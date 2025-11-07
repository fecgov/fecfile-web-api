from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, _view):
        return request.user is not None and request.user.is_staff