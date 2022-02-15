from fecfiler.authentication.auth_enum import Roles


def is_not_treasurer(request):
    is_allowed = False
    if request.method == "GET":
        is_allowed = True
    elif (
        request.user.role == Roles.C_ADMIN.value
        or request.user.role == Roles.BC_ADMIN.value
    ):
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_read_only_or_filer_reports(request):
    is_allowed = False
    if request.user.role == Roles.REVIEWER.value:
        if request.method == "GET":
            is_allowed = True
    elif request.user.role != Roles.REVIEWER.value:
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_read_only_or_filer_submit(request):
    is_allowed = False
    if (
        request.user.role != Roles.REVIEWER.value
        or request.user.role != Roles.EDITOR.value
    ):
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_not_read_only_or_filer(request):
    is_allowed = True
    if request.user.role == Roles.REVIEWER.value:
        is_allowed = False
    return is_allowed
