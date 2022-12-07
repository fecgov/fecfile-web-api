from rest_framework import permissions


class IsAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, account):
        if request.session.get('user_id'):
            return account.pk == request.session.get('user_id')
        return False
