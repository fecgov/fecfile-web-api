from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from .models import Contact
from .serializers import ContactSerializer
import logging

logger = logging.getLogger(__name__)


class ContactViewSet(CommitteeOwnedViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    serializer_class = ContactSerializer
    permission_classes = []

    """Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limmited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """
    queryset = Contact.objects.all().order_by("-id")
