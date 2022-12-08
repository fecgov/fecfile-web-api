from .models import Account

class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.session and request.session.get('user_id')):
            request.user = Account.objects.get(pk=request.session.get('user_id'))

        return self.get_response(request)
