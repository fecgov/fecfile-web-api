from rest_framework.exceptions import ValidationError
from django.http import HttpResponseServerError
from fecfiler.oidc.utils import delete_user_logged_in_cookies
from rest_framework.views import exception_handler
import structlog
import json

logger = structlog.get_logger(__name__)


def _safe_log_value(value):
    if value is None:
        return "None"

    if isinstance(value, BaseException):
        detail = getattr(value, "detail", None)
        if isinstance(detail, (dict, list, tuple, set)):
            try:
                return json.dumps(detail, default=str, sort_keys=True)
            except TypeError:
                return str(detail)
        elif getattr(value, "args", None):
            value = value.args[0] if len(value.args) == 1 else value.args

    if isinstance(value, (dict, list, tuple, set)):
        try:
            return json.dumps(value, default=str, sort_keys=True)
        except TypeError:
            pass
    return str(value)

def _is_safe_for_exception_logging(exc):
    if not isinstance(exc, BaseException):
        return False

    detail = getattr(exc, "detail", None)
    if isinstance(detail, (dict, list, tuple, set)):
        return False

    for arg in getattr(exc, "args", ()):
        if isinstance(arg, (dict, list, tuple, set)):
            return False

    return True

def custom_exception_handler(exc, context):
    if _is_safe_for_exception_logging(exc):
        logger.exception(_safe_log_value(exc))
    else:
        logger.error("Exception: %s", _safe_log_value(exc))
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

    # Do not allow an error response body unless validation
    data = getattr(response, "data")
    exception_type = type(exc)
    logger.error(f"Error: {data}")
    if data and exception_type is not ValidationError:
        response.data = None

    return response


def save_copy(instance, data={}, links={}):
    if instance:
        for field, value in data.items():
            setattr(instance, field, value)
        instance.pk = None
        instance.id = None
        instance._state.adding = True
        instance.save()
        for link_name, link in links.items():
            getattr(instance, link_name).set(link)
        return instance
    return None
