import structlog


class HeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["cache-control"] = "no-cache, no-store"
        return response


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
