from fecfiler.authentication.views import delete_user_logged_in_cookies
from rest_framework.views import exception_handler
from django.http import HttpResponseServerError


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    if response is None:
        return HttpResponseServerError()

    # Delete user cookies on forbidden http response.
    # this will ensure that when the user is redirected
    # to the login page due to the 403, any cookies
    # (such as indicating committee id) are removed to
    # allow for a clean new login.
    if response.status_code == 403:
        delete_user_logged_in_cookies(response)

    # Do not allow an error response body
    if getattr(response, 'data'):
        response.data = None

    return response
