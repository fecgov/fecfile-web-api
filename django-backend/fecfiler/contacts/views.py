import logging
import re
from urllib.parse import urlencode

import requests
from django.db.models import CharField, Q, Value, Count
from django.db.models.functions import Concat, Lower
from django.http import HttpResponseBadRequest, JsonResponse
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.settings import (
    FEC_API_CANDIDATE_LOOKUP_ENDPOINT,
    FEC_API_COMMITTEE_LOOKUP_ENDPOINT,
    FEC_API_KEY,
)
from rest_framework.decorators import action
from rest_framework import filters

from .models import Contact
from .serializers import ContactSerializer

logger = logging.getLogger(__name__)

default_max_fec_results = 10
default_max_fecfile_results = 10
max_allowed_results = 100
NAME_CLAUSE = Concat("first_name", Value(" "), "last_name", output_field=CharField())
NAME_REVERSED_CLAUSE = Concat(
    "last_name", Value(" "), "first_name", output_field=CharField()
)


class ContactViewSet(CommitteeOwnedViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    serializer_class = ContactSerializer

    """Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limmited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    queryset = (
        Contact.objects.annotate(transaction_count=Count("transaction"))
        .alias(
            sort_name=Concat(
                "name", "last_name", Value(" "), "first_name", output_field=CharField()
            )
        )
        .all()
    )
    filter_backends = [filters.OrderingFilter]

    ordering_fields = [
        "sort_name",
        "first_name",
        "type",
        "employer",
        "occupation",
        "id",
    ]
    ordering = ["-created"]

    @action(detail=False)
    def candidate_lookup(self, request):
        q = request.GET.get("q")
        if q is None:
            return HttpResponseBadRequest()

        max_fecfile_results, max_fec_results = self.get_max_results(request)

        params = urlencode({"q": q, "api_key": FEC_API_KEY})
        json_results = requests.get(
            FEC_API_CANDIDATE_LOOKUP_ENDPOINT, params=params
        ).json()

        tokens = list(filter(None, re.split("[^\\w+]", q)))
        term = (".*" + ".* .*".join(tokens) + ".*").lower()
        fecfile_candidates = list(
            self.get_queryset()
            .annotate(
                full_name_fwd=Lower(NAME_CLAUSE),
                full_name_bwd=Lower(NAME_REVERSED_CLAUSE),
            )
            .filter(
                Q(type="CAN")
                & (
                    Q(candidate_id__icontains=q)
                    | (Q(full_name_fwd__regex=term) | Q(full_name_bwd__regex=term))
                )
            )
            .values()
            .order_by("-candidate_id")
        )
        fec_api_candidates = json_results.get("results", [])
        fec_api_candidates = [
            fac
            for fac in fec_api_candidates
            if not any(fac["id"] == ffc["candidate_id"] for ffc in fecfile_candidates)
        ]
        fec_api_candidates = fec_api_candidates[:max_fec_results]
        fecfile_candidates = fecfile_candidates[:max_fecfile_results]
        return_value = {
            "fec_api_candidates": fec_api_candidates,
            "fecfile_candidates": fecfile_candidates,
        }

        return JsonResponse(return_value)

    @action(detail=False)
    def committee_lookup(self, request):
        q = request.GET.get("q")
        if q is None:
            return HttpResponseBadRequest()

        max_fecfile_results, max_fec_results = self.get_max_results(request)

        params = urlencode({"q": q, "api_key": FEC_API_KEY})
        json_results = requests.get(
            FEC_API_COMMITTEE_LOOKUP_ENDPOINT, params=params
        ).json()

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

        max_fecfile_results, _ = self.get_max_results(request)

        fecfile_individuals = list(
            self.get_queryset()
            .annotate(
                full_name_fwd=Lower(NAME_CLAUSE),
                full_name_bwd=Lower(NAME_REVERSED_CLAUSE),
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

        max_fecfile_results, _ = self.get_max_results(request)

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

    def get_max_results(self, request):
        max_fecfile_results = self.get_int_param_value(
            request,
            "max_fecfile_results",
            default_max_fecfile_results,
            max_allowed_results,
        )

        max_fec_results = self.get_int_param_value(
            request, "max_fec_results", default_max_fec_results, max_allowed_results
        )
        return max_fecfile_results, max_fec_results
