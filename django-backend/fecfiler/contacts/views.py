import logging
import re
from urllib.parse import urlencode

import requests
from django.db.models import CharField, Q, Value, Count
from django.db.models.functions import Concat, Lower
from django.http import HttpResponseBadRequest, JsonResponse
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.settings import FEC_API_COMMITTEE_LOOKUP_ENDPOINT, FEC_API_KEY
from rest_framework.decorators import action

from .models import Contact
from .serializers import ContactSerializer

logger = logging.getLogger(__name__)

default_max_fec_results = 10
default_max_fecfile_results = 10
max_allowed_results = 100


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
    queryset = (
        Contact.objects.annotate(transaction_count=Count("schatransaction"))
        .all()
        .order_by("-created")
    )

    @action(detail=False)
    def committee_lookup(self, request):
        q = request.GET.get("q")
        if q is None:
            return HttpResponseBadRequest()

        max_fec_results = self.get_int_param_value(
            request, "max_fec_results", default_max_fec_results, max_allowed_results
        )

        max_fecfile_results = self.get_int_param_value(
            request,
            "max_fecfile_results",
            default_max_fecfile_results,
            max_allowed_results,
        )

        query_params = urlencode({"q": q, "api_key": FEC_API_KEY})
        url = "{url}?{query_params}".format(
            url=FEC_API_COMMITTEE_LOOKUP_ENDPOINT, query_params=query_params
        )
        json_results = requests.get(url).json()

        fecfile_committees = list(
            self.get_queryset()
            .filter(
                Q(type="COM") & (Q(committee_id__icontains=q) | Q(name__icontains=q))
            )
            .values()
            .order_by("-committee_id")
        )
        fec_api_committees = json_results.get("results", [])
        fec_api_committees = [
            fac
            for fac in fec_api_committees
            if not any(fac["id"] == ffc["committee_id"] for ffc in fecfile_committees)
        ]
        fec_api_committees = fec_api_committees[:max_fec_results]
        fecfile_committees = fecfile_committees[:max_fecfile_results]
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

        tokens = list(filter(None, re.split("[^\\w+]", q)))
        term = (".*" + ".* .*".join(tokens) + ".*").lower()

        max_fecfile_results = self.get_int_param_value(
            request,
            "max_fecfile_results",
            default_max_fecfile_results,
            max_allowed_results,
        )

        fecfile_individuals = list(
            self.get_queryset()
            .annotate(
                full_name_fwd=Lower(
                    Concat(
                        "first_name", Value(" "), "last_name", output_field=CharField()
                    )
                )
            )
            .annotate(
                full_name_bwd=Lower(
                    Concat(
                        "last_name", Value(" "), "first_name", output_field=CharField()
                    )
                )
            )
            .filter(
                Q(type="IND")
                & (Q(full_name_fwd__regex=term) | Q(full_name_bwd__regex=term))
            )
            .values()
            .order_by(Lower("last_name").desc())[:max_fecfile_results]
        )
        return_value = {
            "fecfile_individuals": fecfile_individuals,
        }

        return JsonResponse(return_value)

    @action(detail=False)
    def organization_lookup(self, request):
        q = request.GET.get("q")
        if q is None:
            return HttpResponseBadRequest()

        max_fecfile_results = self.get_int_param_value(
            request,
            "max_fecfile_results",
            default_max_fecfile_results,
            max_allowed_results,
        )

        fecfile_organizations = list(
            self.get_queryset()
            .filter(Q(type="ORG") & Q(name__icontains=q))
            .values()
            .order_by("-name")[:max_fecfile_results]
        )
        return_value = {"fecfile_organizations": fecfile_organizations}

        return JsonResponse(return_value)

    def get_int_param_value(
        self, request, param_name: str, default_param_value: int, max_param_value: int
    ):
        if request:
            param_val = request.GET.get(param_name, "")
            if param_val and param_val.isnumeric():
                param_int_val = int(param_val)
                if param_int_val <= max_param_value:
                    return param_int_val
                return max_param_value
        return default_param_value
