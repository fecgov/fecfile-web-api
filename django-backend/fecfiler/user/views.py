from rest_framework import viewsets
from rest_framework.decorators import action
from .serializers import CurrentUserSerializer
from django.http import HttpResponseBadRequest
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.GenericViewSet):
    @action(detail=False, methods=["PUT"], serializer_class=CurrentUserSerializer)
    def current(self, request):
        if request.method == 'PUT':
            serializer = self.get_serializer(request.user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return HttpResponseBadRequest()
