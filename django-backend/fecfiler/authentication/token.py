import warnings
from calendar import timegm
from datetime import datetime
from fecfiler.settings import SECRET_KEY
import jwt
from rest_framework_simplejwt.models.TokenUser import get_username
from rest_framework_simplejwt.settings import api_settings
from rest_framework_jwt.settings import settings
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


def login_dot_gov_logout(request):
    client_id = settings.OIDC_RP_CLIENT_ID
    post_logout_redirect_uri = settings.LOGOUT_REDIRECT_URL
    state = request.get_signed_cookie('oidc_state')

    params = {
        'client_id': client_id,
        'post_logout_redirect_uri': post_logout_redirect_uri,
        'state': state,
    }
    query = urlencode(params)
    op_logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT
    redirect_url = '{url}?{query}'.format(url=op_logout_url, query=query)

    return redirect_url


def generate_username(uuid):
    return uuid


def jwt_payload_handler(user):
    username = get_username(user)

    payload = {
        "user_id": user.pk,
        "email": user.email,
        "username": username,
        "role": user.role,
        "exp": datetime.utcnow() + api_settings.ACCESS_TOKEN_LIFETIME,
    }

    payload["username_field"] = username

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.ROTATE_REFRESH_TOKENS:
        payload["orig_iat"] = timegm(datetime.utcnow().utctimetuple())

    if api_settings.AUDIENCE is not None:
        payload["aud"] = api_settings.AUDIENCE

    if api_settings.ISSUER is not None:
        payload["iss"] = api_settings.ISSUER

    return payload


def verify_token(token_received):
    options = {
        "verify_exp": True,  # Skipping expiration date check
        "verify_aud": False,
    }  # Skipping audience check
    payload = jwt.decode(
        token_received, key=SECRET_KEY, algorithms="HS256", options=options
    )
    return payload


def token_verification(request):
    try:
        token_received = request.headers["token"]
        payload = verify_token(token_received)
        return payload
    except Exception as e:
        logger.debug(
            "exception occurred while generating token for email option.", str(e)
        )
        raise e
