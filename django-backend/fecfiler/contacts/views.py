from rest_framework import viewsets, permissions
from .models import Contact
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = []
