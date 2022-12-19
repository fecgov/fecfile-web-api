from fecfiler.authentication.views import delete_user_logged_in_cookies
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None and response.status_code == 403:
        delete_user_logged_in_cookies(response)

    return response
