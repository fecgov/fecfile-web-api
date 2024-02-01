from rest_framework import viewsets
from rest_framework.decorators import action
from .serializers import CurrentUserSerializer
from django.http import HttpResponseBadRequest, HttpResponse
import logging

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.GenericViewSet):
    @action(detail=False, serializer_class=CurrentUserSerializer)
    def current(self, request):
        if request.method == 'GET':
            return request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(request.user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return HttpResponse()
            return HttpResponseBadRequest()
