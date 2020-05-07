def is_not_treasurer(request):
    is_allowed = False
    if request.user.role != 'TREASURER':
        if request.method == 'GET':
            is_allowed = True
    elif request.user.role == 'TREASURER':
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_read_only_or_filer_reports(request):
    is_allowed = False
    if request.user.role == 'READONLY' or request.user.role == 'UPLOADER':
        if request.method == 'GET':
            is_allowed = True
    elif request.user.role != 'READONLY' and request.user.role != 'UPLOADER':
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_read_only_or_filer_submit(request):
    is_allowed = False
    if request.user.role != 'READONLY' or request.user.role != 'ENTRY':
        is_allowed = True
    if not is_allowed:
        raise Exception("User is not allowed to access this API ")


def is_not_read_only_or_filer(request):
    is_allowed = True
    if request.user.role == 'READONLY' or request.user.role == 'UPLOADER':
        is_allowed = False
    return is_allowed
