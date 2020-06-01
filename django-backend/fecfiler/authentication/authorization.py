def is_not_treasurer(request):
    is_allowed = False
    if request.method == 'GET':
        is_allowed = True
    elif request.user.role == 'C_ADMIN' or request.user.role == 'BC_ADMIN':
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_read_only_or_filer_reports(request):
    is_allowed = False
    if request.user.role == 'REVIEWER':
        if request.method == 'GET':
            is_allowed = True
    elif request.user.role != 'REVIEWER':
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_read_only_or_filer_submit(request):
    is_allowed = False
    if request.user.role != 'REVIEWER' or request.user.role != 'EDITOR':
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_not_read_only_or_filer(request):
    is_allowed = True
    if request.user.role == 'REVIEWER':
        is_allowed = False
    return is_allowed
