from rest_framework import viewsets
from rest_framework.decorators import action
from fecfiler.web_services.tasks import create_dot_fec


class WebServicesViewSet(viewsets.ViewSet):
    """
    A viewset that provides actions to start web service tasks and
    retrieve thier statuses and results
    """

    @action(detail=False, methods=["post"], url_path="create-dot-fec")
    def create_dot_fec(self, request):
        create_dot_fec.delay(request.data)
