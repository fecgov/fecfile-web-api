from django.http import (
    HttpResponseRedirect,
    JsonResponse,
    HttpResponseBadRequest,
)
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)

from fecfiler.oidc.utils import idp_base64_encode_left_128_bits_of_str
from fecfiler.settings import MOCK_OIDC_PROVIDER_CACHE
from drf_spectacular.utils import extend_schema
from jwcrypto import jwk
import structlog
from uuid import uuid4
from secrets import token_urlsafe
import jwt
import time
import re
import json
import redis
import structlog

logger = structlog.get_logger(__name__)

if MOCK_OIDC_PROVIDER_CACHE:
    redis_instance = redis.Redis.from_url(MOCK_OIDC_PROVIDER_CACHE)
else:
    raise SystemError("SYSTEM_STATUS_CACHE_BACKEND is not set")

MOCK_OIDC_PROVIDER_DATA = "MOCK_OIDC_PROVIDER_DATA"
MOCK_OIDC_PROVIDER_KDAT = "MOCK_OIDC_PROVIDER_KDAT"

logger = structlog.get_logger(__name__)

test_username = "c34867d9-3a41-43ff-ae25-ca498f64b52d"
test_email = "test@test.com"


@extend_schema(exclude=True)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET"])
def discovery(request):
    retval = {
        "authorization_endpoint": request.build_absolute_uri(reverse("authorize")),
        "issuer": request.build_absolute_uri().replace(request.path, ""),
        "jwks_uri": request.build_absolute_uri(reverse("certs")),
        "token_endpoint": request.build_absolute_uri(reverse("token")),
        "userinfo_endpoint": request.build_absolute_uri(reverse("userinfo")),
        "end_session_endpoint": request.build_absolute_uri(reverse("logout")),
    }
    return JsonResponse(retval)


@extend_schema(exclude=True)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET"])
def certs(request):
    kdat_dict = get_or_create_kdat_dict()
    pubkey_str = kdat_dict.get("pubkey")
    retval = {"keys": [{**(json.loads(pubkey_str))}]}
    return JsonResponse(retval)


@extend_schema(exclude=True)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET"])
def authorize(request):
    if (
        "redirect_uri" not in request.query_params
        or "state" not in request.query_params
        or "nonce" not in request.query_params
    ):
        return HttpResponseBadRequest(
            "redirect_uri, state, nonce query params are required"
        )
    redirect_uri = request.query_params.get("redirect_uri")
    state = request.query_params.get("state")
    nonce = request.query_params.get("nonce")
    code = token_urlsafe(32)

    auth_data = {
        "code": code,
        "nonce": nonce,
        "access_token": token_urlsafe(32),
    }
    redis_instance.set(MOCK_OIDC_PROVIDER_DATA, json.dumps(auth_data), ex=3600)

    retval = f"{redirect_uri}?code={code}&state={state}"
    return HttpResponseRedirect(retval)


@extend_schema(exclude=True)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["POST"])
def token(request):
    auth_data = json.loads(redis_instance.get(MOCK_OIDC_PROVIDER_DATA))
    code = auth_data.get("code")
    if not code:
        return HttpResponseBadRequest("call to authorize endpoint is required first")
    request_code = request.data.get("code")
    if request_code != code:
        return HttpResponseBadRequest("authorize code is invalid")

    nonce = auth_data.get("nonce")
    access_token = auth_data.get("access_token")
    token_type = "Bearer"
    expires_in = 3600
    at_hash = idp_base64_encode_left_128_bits_of_str(access_token)
    c_hash = idp_base64_encode_left_128_bits_of_str(code)
    args = {
        "iss": request.build_absolute_uri().replace(request.path, ""),
        "sub": test_username,
        "aud": "test_client_id",
        "acr": "test_acr",
        "at_hash": at_hash,
        "c_hash": c_hash,
        "exp": time.time() + 60,
        "iat": time.time(),
        "jti": "test_jti",
        "nbf": time.time(),
        "nonce": nonce,
    }
    kdat_dict = get_or_create_kdat_dict()
    id_token = jwt.encode(
        args,
        kdat_dict.get("pvtkey"),
        algorithm="RS256",
        headers={"kid": kdat_dict.get("kid")},
    )

    retval = {
        "access_token": access_token,
        "token_type": token_type,
        "expires_in": expires_in,
        "id_token": id_token,
    }
    return JsonResponse(retval)


@extend_schema(exclude=True)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET"])
def userinfo(request):
    auth_data = json.loads(redis_instance.get(MOCK_OIDC_PROVIDER_DATA))
    if "Authorization" not in request.headers:
        logger.error("Authorization header is required")
        return HttpResponseBadRequest("Authorization header is required")
    if not auth_data.get("access_token"):
        logger.error("all to authorize endpoint is required first")
        return HttpResponseBadRequest("call to authorize endpoint is required first")
    auth_header = request.headers.get("Authorization")
    match = re.search("Bearer (.+)", auth_header)
    if not match:
        logger.error("Bearer token not found")
        return HttpResponseBadRequest("Bearer token not found")
    if match.group(1) != auth_data.get("access_token"):
        logger.error("Invalid Bearer token")
        return HttpResponseBadRequest("Invalid Bearer token")

    retval = {
        "sub": test_username,
        "email": test_email,
    }
    return JsonResponse(retval)


@extend_schema(exclude=True)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET"])
def logout(request):
    if "post_logout_redirect_uri" not in request.query_params:
        return HttpResponseBadRequest("post_logout_redirect_uri param is required")
    post_logout_redirect_uri = request.query_params.get("post_logout_redirect_uri")
    state = request.query_params.get("state", None)
    redis_instance.delete(MOCK_OIDC_PROVIDER_DATA)

    retval = post_logout_redirect_uri
    if state:
        retval += f"?state={state}"
    return HttpResponseRedirect(retval)


def get_or_create_kdat_dict():
    kdat = redis_instance.get(MOCK_OIDC_PROVIDER_KDAT)
    if not kdat:
        test_kid = str(uuid4())
        rsapair = jwk.JWK.generate(
            kty="RSA", size=2048, kid=test_kid, use="sig", alg="RS256"
        )
        pubkey = rsapair.export_public()
        pvtkey_pem = rsapair.export_to_pem(True, None).decode()
        kdat = json.dumps({"kid": test_kid, "pubkey": pubkey, "pvtkey": pvtkey_pem})
        redis_instance.set(MOCK_OIDC_PROVIDER_KDAT, kdat, ex=3600)
    return json.loads(kdat)
