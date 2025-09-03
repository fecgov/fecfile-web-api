import requests
from fecfiler.settings import (
    OIDC_OP_AUTODISCOVER_ENDPOINT,
)
import structlog

logger = structlog.getLogger(__name__)


OIDC_OP_CONFIG = None


def get_oidc_op_config():
    global OIDC_OP_CONFIG
    if not OIDC_OP_CONFIG:
        OIDC_OP_CONFIG = requests.get(OIDC_OP_AUTODISCOVER_ENDPOINT).json()
    return OIDC_OP_CONFIG


def get_jwks_endpoint():
    return get_oidc_op_config().get("jwks_uri")


def get_authorization_endpoint():
    return get_oidc_op_config().get("authorization_endpoint")


def get_token_endpoint():
    return get_oidc_op_config().get("token_endpoint")


def get_user_endpoint():
    return get_oidc_op_config().get("userinfo_endpoint")


def get_logout_endpoint():
    return get_oidc_op_config().get("end_session_endpoint")
