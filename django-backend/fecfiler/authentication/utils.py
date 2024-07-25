import logging


from fecfiler.settings import (
    FFAPI_LOGIN_DOT_GOV_COOKIE_NAME,
    FFAPI_COOKIE_DOMAIN,
    FFAPI_TIMEOUT_COOKIE_NAME,
)

LOGGER = logging.getLogger(__name__)


def delete_user_logged_in_cookies(response):
    response.delete_cookie(FFAPI_LOGIN_DOT_GOV_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie(FFAPI_TIMEOUT_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie("oidc_state")
    response.delete_cookie("csrftoken", domain=FFAPI_COOKIE_DOMAIN)
