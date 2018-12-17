import json
from django.contrib.auth import authenticate, login, logout
from rest_framework import permissions, viewsets, status, views
from rest_framework.response import Response
from .models import Account
from .permissions import IsAccountOwner
from .serializers import AccountSerializer
from fecfiler.forms.models import Committee

from rest_framework_jwt.settings import api_settings

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


def jwt_response_payload_handler(token, user=None, request=None):
    """
    JWT TOKEN handler. 
    Checks if Committee ID exists in forms.models.Committee first before allowing access.
    """
    if not Committee.objects.filter(committeeid=user.username).exists():
        return {
            'status': 'Unauthorized',
            'message': 'This account has not been authorized.'
        }
    
    return {
        'token': token       
    }

#payload = jwt_response_payload_handler(user)
#token = jwt_encode_handler(payload)

class AccountViewSet(viewsets.ModelViewSet):
    lookup_field = 'username'
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return permissions.AllowAny(),
        if self.request.method == 'POST':
            return permissions.AllowAny(),
        return permissions.IsAuthenticated(), IsAccountOwner()

    def create(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            Account.objects.create_user(**serializer.validated_data)
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'Bad request',
            'message': 'Account could not be created with received data.',
            'details': str(serializer.errors),
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(views.APIView):

    def post(self, request, format=None):
        data = request.data
        username = data.get('username', None)
        password = data.get('password', None)
        #import ipdb; ipdb.set_trace()
        account = authenticate(request=request, username=username, password=password)

        # fail, bad login info
        if account is None:
            return Response({
                'status': 'Unauthorized',
                'message': 'ID/Password combination invalid.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # fail, inactive account
        if not account.is_active:
            return Response({
                'status': 'Unauthorized',
                'message': 'This account has been disabled.'
            }, status=status.HTTP_401_UNAUTHORIZED)


        if not Committee.objects.filter(committeeid=username).exists():
            return Response({
                'status': 'Unauthorized',
                'message': 'This account has not been authorized.'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        # success, login and respond
        login(request, account)
        serialized = AccountSerializer(account)
        return Response(serialized.data)


class LogoutView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        logout(request)
        return Response({}, status=status.HTTP_204_NO_CONTENT)
