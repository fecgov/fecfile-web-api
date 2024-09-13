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

from fecfiler.settings import MOCK_OIDC_PROVIDER_CACHE

from jwcrypto import jwk
import structlog
from uuid import uuid4
from secrets import token_urlsafe
import jwt
import time
import re
import json
import redis

if MOCK_OIDC_PROVIDER_CACHE:
    redis_instance = redis.Redis.from_url(MOCK_OIDC_PROVIDER_CACHE)
else:
    raise SystemError("SYSTEM_STATUS_CACHE_BACKEND is not set")

MOCK_OIDC_PROVIDER_DATA = "MOCK_OIDC_PROVIDER_DATA"

logger = structlog.get_logger(__name__)

test_username = "c34867d9-3a41-43ff-ae25-ca498f64b52d"
test_email = "test@test.com"

test_kid = str(uuid4())
rsapair = jwk.JWK.generate(kty="RSA", size=2048, kid=test_kid, use="sig", alg="RS256")
pubkey = rsapair.export_public(True)
pvtkey_pem = rsapair.export_to_pem(True, None).decode()


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


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET"])
def certs(request):
    retval = {"keys": [{**pubkey}]}
    return JsonResponse(retval)


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


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["POST"])
def token(request):
    auth_data = json.loads(redis_instance.get(MOCK_OIDC_PROVIDER_DATA))
    if not auth_data.get("code"):
        return HttpResponseBadRequest("call to authorize endpoint is required first")
    request_code = request.data.get("code")
    if request_code != auth_data.get("code"):
        return HttpResponseBadRequest("authorize code is invalid")

    nonce = auth_data.get("nonce")
    access_token = auth_data.get("access_token")
    token_type = "Bearer"
    expires_in = 3600
    args = {
        "iss": request.build_absolute_uri().replace(request.path, ""),
        "sub": test_username,
        "aud": "test_client_id",
        "acr": "test_acr",
        "at_hash": "test_at_hash",
        "c_hash": "test_c_hash",
        "exp": time.time() + 60,
        "iat": time.time(),
        "jti": "test_jti",
        "nbf": time.time(),
        "nonce": nonce,
    }
    id_token = jwt.encode(
        args,
        pvtkey_pem,
        algorithm="RS256",
        headers={"kid": test_kid},
    )

    retval = {
        "access_token": access_token,
        "token_type": token_type,
        "expires_in": expires_in,
        "id_token": id_token,
    }
    return JsonResponse(retval)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET"])
def userinfo(request):
    auth_data = json.loads(redis_instance.get(MOCK_OIDC_PROVIDER_DATA))
    if "Authorization" not in request.headers:
        return HttpResponseBadRequest("Authorization header is required")
    if not auth_data.get("access_token"):
        return HttpResponseBadRequest("call to authorize endpoint is required first")
    auth_header = request.headers.get("Authorization")
    match = re.search("Bearer (.+)", auth_header)
    if not match:
        return HttpResponseBadRequest("Bearer token not found")
    if match.group(1) != auth_data.get("access_token"):
        return HttpResponseBadRequest("Invalid Bearer token")

    retval = {
        "sub": test_username,
        "email": test_email,
    }
    return JsonResponse(retval)


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
