"""
This source code has been copied from the mozilla-django-oidc
project:
https://mozilla-django-oidc.readthedocs.io/en/stable/index.html#
https://github.com/mozilla/mozilla-django-oidc/tree/main

It has been modified in places to meet the needs of the project and
the original version can be found on Github:
https://github.com/mozilla/mozilla-django-oidc/blob/main/mozilla_django_oidc/auth.py
"""

import json
import logging
import requests

# logindotgov-oidc
import secrets
import time
import jwt

# /logindotgov-oidc
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import SuspiciousOperation
from django.urls import reverse
from django.utils.encoding import force_bytes, smart_bytes, smart_str
from josepy.jwk import JWK
from josepy.jws import JWS, Header
from requests.exceptions import HTTPError

from . import oidc_op_config

from django.conf import settings

LOGGER = logging.getLogger(__name__)


class OIDCAuthenticationBackend(ModelBackend):
    """Override Django's authentication."""

    def __init__(self, *args, **kwargs):
        self.UserModel = get_user_model()

    def get_idp_unique_id_value(self, claims):
        """Helper method to clarify whether we're using OP or RP unique ID"""
        retval = claims.get(settings.OIDC_OP_UNIQUE_IDENTIFIER)
        if not retval:
            msg = (
                "Failed to retrieve OIDC_OP_UNIQUE_IDENTIFIER "
                f"{settings.OIDC_OP_UNIQUE_IDENTIFIER} from claims"
            )
            raise SuspiciousOperation(msg)
        return retval

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified unique identifier."""
        # Get the unique ID value from IDP
        unique_identifier_value = self.get_idp_unique_id_value(claims)
        if not unique_identifier_value:
            return self.UserModel.objects.none()
        # Use the app label to filter
        filter_label = settings.OIDC_RP_UNIQUE_IDENTIFIER + "__iexact"
        kwargs = {filter_label: unique_identifier_value}
        filtered_users = self.UserModel.objects.filter(**kwargs)

        return filtered_users

    def verify_claims(self, claims):
        """Verify the provided claims to decide if authentication should be allowed."""
        return "email" in claims

    def create_user(self, claims):
        """Return object for a newly created user account."""
        email = claims.get("email")
        username = self.get_username(claims)
        return self.UserModel.objects.create_user(username, email=email)

    def get_username(self, claims):
        """Generate username based on claims."""
        return self.get_idp_unique_id_value(claims)

    def update_user(self, user, claims):
        """Update existing user with new email, if necessary save, and return user"""

        user.email = claims.get("email")
        user.save()
        return user

    def _verify_jws(self, payload, key):
        """Verify the given JWS payload with the given key and return the payload"""
        jws = JWS.from_compact(payload)

        try:
            alg = jws.signature.combined.alg.name
        except AttributeError:
            msg = "No alg value found in header"
            raise SuspiciousOperation(msg)

        if alg != settings.OIDC_RP_SIGN_ALGO:
            msg = (
                "The provider algorithm {!r} does not match the client's "
                "OIDC_RP_SIGN_ALGO.".format(alg)
            )
            raise SuspiciousOperation(msg)

        if isinstance(key, str):
            # Use smart_bytes here since the key string comes from settings.
            jwk = JWK.load(smart_bytes(key))
        else:
            # The key is a json returned from the IDP JWKS endpoint.
            jwk = JWK.from_json(key)

        if not jws.verify(jwk):
            msg = "JWS token verification failed."
            raise SuspiciousOperation(msg)

        return jws.payload

    def retrieve_matching_jwk(self, token):
        """Get the signing key by exploring the JWKS endpoint of the OP."""
        response_jwks = requests.get(
            oidc_op_config.get_jwks_endpoint(),
            verify=True,
            timeout=None,
            proxies=None,
        )
        response_jwks.raise_for_status()
        jwks = response_jwks.json()

        # Compute the current header from the given token to find a match
        jws = JWS.from_compact(token)
        json_header = jws.signature.protected
        header = Header.json_loads(json_header)

        key = None
        for jwk in jwks["keys"]:
            if jwk["kid"] != smart_str(header.kid):
                continue
            if "alg" in jwk and jwk["alg"] != smart_str(header.alg):
                continue
            key = jwk
        if key is None:
            raise SuspiciousOperation("Could not find a valid JWKS.")
        return key

    def get_payload_data(self, token, key):
        """Helper method to get the payload of the JWT token."""
        return self._verify_jws(token, key)

    def verify_token(self, token, **kwargs):
        """Validate the token signature."""
        nonce = kwargs.get("nonce")

        token = force_bytes(token)
        key = self.retrieve_matching_jwk(token)
        payload_data = self.get_payload_data(token, key)

        # The 'token' will always be a byte string since it's
        # the result of base64.urlsafe_b64decode().
        # The payload is always the result of base64.urlsafe_b64decode().
        # In Python 3 and 2, that's always a byte string.
        # In Python3.6, the json.loads() function can accept a byte string
        # as it will automagically decode it to a unicode string before
        # deserializing https://bugs.python.org/issue17909
        payload = json.loads(payload_data.decode("utf-8"))
        token_nonce = payload.get("nonce")

        if nonce != token_nonce:
            msg = "JWT Nonce verification failed. "
            raise SuspiciousOperation(msg)

    def get_token(self, payload):
        """Return token object as a dictionary.
        Borrowed from logindotgov-oidc, modified
        https://github.com/trussworks/logindotgov-oidc-py
        """
        jwt_args = {
            "iss": settings.OIDC_RP_CLIENT_ID,
            "sub": settings.OIDC_RP_CLIENT_ID,
            "aud": oidc_op_config.get_token_endpoint(),
            "jti": secrets.token_hex(16),
            "exp": int(time.time()) + 300,  # 5 minutes from now
        }
        # Client secret needs to be pem-encoded string
        encoded_jwt = (
            jwt.encode(
                jwt_args,
                settings.OIDC_RP_CLIENT_SECRET,
                algorithm=settings.OIDC_RP_SIGN_ALGO,
            )
            if settings.OIDC_RP_CLIENT_SECRET and settings.OIDC_RP_SIGN_ALGO
            else None
        )
        token_payload = {
            "client_assertion": encoded_jwt,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",  # noqa
            "code": payload.get("code"),
            "grant_type": "authorization_code",
        }
        response = requests.post(oidc_op_config.get_token_endpoint(), data=token_payload)
        self.raise_token_response_error(response)
        return response.json()

    def raise_token_response_error(self, response):
        """Raises :class:`HTTPError`, if one occurred.
        as per: https://datatracker.ietf.org/doc/html/rfc6749#section-5.2
        """
        # if there wasn't an error all is good
        if response.status_code == 200:
            return
        # otherwise something is up...
        http_error_msg = (
            f"Get Token Error (url: {response.url}, "
            f"status: {response.status_code}, "
            f"body: {response.text})"
        )
        raise HTTPError(http_error_msg, response=response)

    def get_userinfo(self, access_token):
        """Return user details dictionary. The id_token and payload are not used in
        the default implementation, but may be used when overriding this method"""

        user_response = requests.get(
            oidc_op_config.get_user_endpoint(),
            headers={"Authorization": "Bearer {0}".format(access_token)},
            verify=True,
            timeout=None,
            proxies=None,
        )
        user_response.raise_for_status()
        return user_response.json()

    def authenticate(self, request, **kwargs):
        """Authenticates a user based on the OIDC code flow."""

        self.request = request
        if not self.request:
            return None

        state = self.request.GET.get("state")
        code = self.request.GET.get("code")
        nonce = kwargs.pop("nonce", None)

        if not code or not state:
            return None

        token_payload = {
            "client_id": settings.OIDC_RP_CLIENT_ID,
            "client_secret": settings.OIDC_RP_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.request.build_absolute_uri(reverse("oidc_callback")),
        }

        # Get the token
        token_info = self.get_token(token_payload)
        id_token = token_info.get("id_token")
        access_token = token_info.get("access_token")

        # Validate the token
        self.verify_token(id_token, nonce=nonce)

        return self.get_or_create_user(access_token)

    def get_or_create_user(self, access_token):
        """Returns a User instance if 1 user is found. Creates a user if not found
        and configured to do so. Returns nothing if multiple users are matched."""

        user_info = self.get_userinfo(access_token)

        claims_verified = self.verify_claims(user_info)
        if not claims_verified:
            msg = "Claims verification failed"
            raise SuspiciousOperation(msg)

        # unique identifier-based filtering
        users = self.filter_users_by_claims(user_info)

        if len(users) == 1:
            return self.update_user(users[0], user_info)
        elif len(users) > 1:
            # In the rare case that two user accounts have the same unique identifier,
            # bail. Randomly selecting one seems really wrong.
            msg = "Multiple users returned"
            raise SuspiciousOperation(msg)
        else:
            user = self.create_user(user_info)
            return user

    def get_user(self, user_id):
        """Return a user based on the id."""

        try:
            return self.UserModel.objects.get(pk=user_id)
        except self.UserModel.DoesNotExist:
            return None
