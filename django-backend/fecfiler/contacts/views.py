from django.http import HttpResponseBadRequest, JsonResponse
from django.db.models import Q
from django.db.models.functions import Lower
from rest_framework.decorators import action
from fecfiler.settings import FEC_API_KEY, FEC_API_COMMITTEE_LOOKUP_ENDPOINT
from urllib.parse import urlencode
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from .models import Contact
from .serializers import ContactSerializer
import requests
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

    @action(detail=False)
    def committee_lookup(self, request):
        q = request.GET.get("q")
        if q is None:
            return HttpResponseBadRequest()

        max_fec_results = 10
        max_fec_results_param = request.GET.get("max_fec_results", "")
        if max_fec_results_param is not None and max_fec_results_param.isnumeric():
            max_fec_results = int(max_fec_results_param)

        max_fecfile_results = 10
        max_fecfile_results_param = request.GET.get("max_fecfile_results", "")
        if (
            max_fecfile_results_param is not None
            and max_fecfile_results_param.isnumeric()
        ):
            max_fecfile_results = int(max_fecfile_results_param)

        query_params = urlencode(
            {
                "q": q,
                "api_key": FEC_API_KEY,
            }
        )
        url = "{url}?{query_params}".format(
            url=FEC_API_COMMITTEE_LOOKUP_ENDPOINT, query_params=query_params
        )
        json_results = requests.get(url).json()

        fec_api_committees = json_results.get("results", [])[:max_fec_results]
        fecfile_committees = list(
            self.get_queryset()
            .filter(Q(committee_id__icontains=q) | Q(name__icontains=q))
            .values()
            .order_by("-committee_id")[:max_fecfile_results]
        )
        return_value = {
            "fec_api_committees": fec_api_committees,
            "fecfile_committees": fecfile_committees,
        }

        return JsonResponse(return_value)

    @action(detail=False)
    def individual_lookup(self, request):
        q = request.GET.get("q")
        if q is None:
            return HttpResponseBadRequest()

        max_fecfile_results = 10
        max_fecfile_results_param = request.GET.get("max_fecfile_results", "")
        if (
            max_fecfile_results_param is not None
            and max_fecfile_results_param.isnumeric()
        ):
            max_fecfile_results = int(max_fecfile_results_param)

        fecfile_individuals = list(
            self.get_queryset()
            .filter(Q(type__icontains="IND") & (
                    Q(last_name__icontains=q) | Q(first_name__icontains=q)))
            .values()
            .order_by(Lower("last_name").desc())[:max_fecfile_results]
        )
        return_value = {
            "fecfile_individuals": fecfile_individuals,
        }

        return JsonResponse(return_value)
