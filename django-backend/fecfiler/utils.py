from rest_framework.exceptions import ValidationError
from django.http import HttpResponseServerError
from fecfiler.authentication.views import delete_user_logged_in_cookies
from rest_framework.views import exception_handler
import structlog

logger = structlog.get_logger(__name__)


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.

    response = exception_handler(exc, context)

    if response is None:
        logger.error(f"Error: {exc}")
        return HttpResponseServerError()

    # Delete user cookies on forbidden http response.
    # this will ensure that when the user is redirected
    # to the login page due to the 403, any cookies
    # (such as indicating committee id) are removed to
    # allow for a clean new login.
    if response.status_code == 403:
        delete_user_logged_in_cookies(response)

    # Do not allow an error response body unless validation
    data = getattr(response, "data")
    exception_type = type(exc)
    logger.error(f"Error: {data}")
    if data and exception_type is not ValidationError:
        response.data = None

    return response


def save_copy(instance, data={}):
    if instance:
        for field, value in data.items():
            setattr(instance, field, value)
        instance.pk = None
        instance.id = None
        instance._state.adding = True
        instance.save()
        return instance
    return None
