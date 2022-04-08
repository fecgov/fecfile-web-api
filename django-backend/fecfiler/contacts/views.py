from rest_framework import viewsets
from .models import Contact
from .serializers import ContactSerializer
import logging

logger = logging.getLogger(__name__)


class ContactViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    # queryset = Contact.objects.all().order_by('-id')
    serializer_class = ContactSerializer
    permission_classes = []

    def get_queryset(self):
        committee_id = self.request.user.cmtee_id
        queryset = Contact.objects.all().filter(
            committee_account_id__committee_id=committee_id
        )
        return queryset.order_by("-id")
