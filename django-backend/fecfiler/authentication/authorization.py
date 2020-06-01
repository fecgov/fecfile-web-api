from fecfiler.authentication.auth_enum import Roles


def is_not_treasurer(request):
    is_allowed = False
    if request.method == 'GET':
        is_allowed = True
    elif request.user.role == Roles.C_ADMIN or request.user.role == Roles.BC_ADMIN:
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_read_only_or_filer_reports(request):
    is_allowed = False
    if request.user.role == Roles.REVIEWER:
        if request.method == 'GET':
            is_allowed = True
    elif request.user.role != Roles.REVIEWER:
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_read_only_or_filer_submit(request):
    is_allowed = False
    if request.user.role != Roles.REVIEWER or request.user.role != Roles.EDITOR:
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_not_read_only_or_filer(request):
    is_allowed = True
    if request.user.role == Roles.REVIEWER:
        is_allowed = False
    return is_allowed
