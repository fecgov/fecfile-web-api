import structlog
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import connections


def _pool_check():
    """Validate all idle pool connections; broken ones are replaced immediately."""
    pool = getattr(connections["default"], "pool", None)
    if pool is not None and hasattr(pool, "_tasks") and not pool.closed:
        pool.check()


class HeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _pool_check()
        response = self.get_response(request)
        response["cache-control"] = "no-cache, no-store"
        return response


class FecfileSessionMiddleware(SessionMiddleware):
    def process_response(self, request, response):
        _pool_check()
        return super().process_response(request, response)


class StructlogContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        committee_uuid = request.session.get("committee_uuid")
        committee_id = request.session.get("committee_id")
        structlog.contextvars.bind_contextvars(
            committee_id=committee_id, committee_uuid=committee_uuid
        )
        response = self.get_response(request)
        return response
