import structlog
import re
from urllib.parse import urlencode
from django.db import transaction
import requests
from django.db.models import CharField, Q, Value
from django.db.models.functions import Concat, Lower, Coalesce
from django.http import HttpResponseBadRequest, JsonResponse
from fecfiler.committee_accounts.views import (
    CommitteeOwnedViewMixin,
)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import mixins, GenericViewSet
from rest_framework import viewsets, pagination, filters, status
from .models import Contact
from .serializers import ContactSerializer
import fecfiler.settings as settings

logger = structlog.get_logger(__name__)

default_max_fec_results = 10
default_max_fecfile_results = 10
max_allowed_results = 100
NAME_CLAUSE = Concat("first_name", Value(" "), "last_name", output_field=CharField())
NAME_REVERSED_CLAUSE = Concat(
    "last_name", Value(" "), "first_name", output_field=CharField()
)

FEC_API_COMMITTEE_LOOKUP_ENDPOINT = (
    str(settings.PRODUCTION_OPEN_FEC_API) + "names/committees/"
)
FEC_API_CANDIDATE_LOOKUP_ENDPOINT = str(settings.PRODUCTION_OPEN_FEC_API) + "candidates/"
FEC_API_CANDIDATE_ENDPOINT = (
    str(settings.PRODUCTION_OPEN_FEC_API) + "candidate/{}/history/"
)


def validate_and_sanitize_candidate(candidate_id):
    if candidate_id is None:
        raise AssertionError("No Candidate ID provided")
    if re.match(r"^[a-zA-Z0-9]{9}$", candidate_id):
        return candidate_id
    else:
        raise AssertionError("Candidate ID provided invalid")


def validate_and_sanitize_committee(committee_id):
    if committee_id is None:
        raise AssertionError("No Committee ID provided")
    if re.match(r"^[a-zA-Z0-9]{9}$", committee_id):
        return committee_id
    else:
        raise AssertionError("Committee ID provided invalid")


class ContactListPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class ContactViewSet(CommitteeOwnedViewMixin, viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    serializer_class = ContactSerializer
    pagination_class = ContactListPagination

    """Note that this ViewSet inherits from CommitteeOwnedViewMixin
    The queryset will be further limmited by the user's committee
    in CommitteeOwnedViewMixin's implementation of get_queryset()
    """

    queryset = Contact.objects.alias(
        sort_name=Concat(
            "name", "last_name", Value(" "), "first_name", output_field=CharField()
        ),
        sort_fec_id=Coalesce("committee_id", "candidate_id"),
    ).all()

    filter_backends = [filters.OrderingFilter]

    ordering_fields = [
        "sort_name",
        "first_name",
        "type",
        "employer",
        "occupation",
        "sort_fec_id",
        "id",
    ]
    ordering = ["-created"]

    @action(detail=False)
    def candidate(self, request):
        candidate_id = request.query_params.get("candidate_id")
        if not candidate_id:
            return HttpResponseBadRequest()
        try:
            sanitized_candidate_id = validate_and_sanitize_candidate(candidate_id)
            headers = {"Content-Type": "application/json"}
            params = {
                "api_key": settings.PRODUCTION_OPEN_FEC_API_KEY,
                "sort": "-two_year_period",
            }
            url = FEC_API_CANDIDATE_ENDPOINT.format(sanitized_candidate_id)
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            response_json = response.json()
            results = response_json["results"]
            return JsonResponse(results[0] if len(results) > 0 else {})
        except AssertionError:
            return HttpResponseBadRequest()

    @action(detail=False)
    def committee(self, request):
        committee_id = request.query_params.get("committee_id")
        if not committee_id:
            return HttpResponseBadRequest()
        try:
            sanitized_committee_id = validate_and_sanitize_committee(committee_id)
            headers = {"Content-Type": "application/json"}
            endpoint = f"{settings.PRODUCTION_OPEN_FEC_API}committee/{sanitized_committee_id}/"  # noqa
            response = requests.get(
                endpoint,
                params={"api_key": settings.PRODUCTION_OPEN_FEC_API_KEY},
                headers=headers,
            )
            response.raise_for_status()

            response_json = response.json()
            results = response_json.get("results")
            if results:
                return JsonResponse(results[0])
            else:
                return JsonResponse({})
        except AssertionError:
            return HttpResponseBadRequest()

    @action(detail=False)
    def candidate_lookup(self, request):
        q = request.GET.get("q")
        if q is None:
            return HttpResponseBadRequest()

        max_fecfile_results, max_fec_results = self.get_max_results(request)
        office = request.GET.get("office", "")
        exclude_fec_ids = (
            request.GET.get("exclude_fec_ids").split(",")
            if request.GET.get("exclude_fec_ids")
            else []
        )
        exclude_ids = (
            request.GET.get("exclude_ids").split(",")
            if request.GET.get("exclude_ids")
            else []
        )
        params = {"q": q, "api_key": settings.PRODUCTION_OPEN_FEC_API_KEY}
        if office:
            params["office"] = office
        params = urlencode(params)
        if len(q) >= 3:
            response = requests.get(FEC_API_CANDIDATE_LOOKUP_ENDPOINT, params=params)
            if response.status_code != status.HTTP_404_NOT_FOUND:
                response.raise_for_status()

            json_results = response.json()
        else:
            json_results = {}

        tokens = list(filter(None, re.split("[^\\w+]", q)))
        term = (".*" + ".* .*".join(tokens) + ".*").lower()
        query_set = (
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
            .exclude(id__in=exclude_ids)
            .values()
            .order_by("-candidate_id")
        )
        if office:
            query_set = query_set.filter(candidate_office=office)
        fecfile_candidates = list(query_set)
        fec_api_candidates = json_results.get("results", [])
        fec_api_candidates = [
            fac
            for fac in fec_api_candidates
            if not any(
                fac["candidate_id"] == ffc["candidate_id"] for ffc in fecfile_candidates
            )
            and fac["candidate_id"] not in exclude_fec_ids
        ]
        return_value = {
            "fec_api_candidates": fec_api_candidates[:max_fec_results],
            "fecfile_candidates": fecfile_candidates[:max_fecfile_results],
        }

        return JsonResponse(return_value)

    @action(detail=False)
    def committee_lookup(self, request):
        q = request.GET.get("q")
        if q is None:
            return HttpResponseBadRequest()

        max_fecfile_results, max_fec_results = self.get_max_results(request)

        exclude_fec_ids = (
            request.GET.get("exclude_fec_ids").split(",")
            if request.GET.get("exclude_fec_ids")
            else []
        )
        exclude_ids = (
            request.GET.get("exclude_ids").split(",")
            if request.GET.get("exclude_ids")
            else []
        )
        params = urlencode({"q": q, "api_key": settings.PRODUCTION_OPEN_FEC_API_KEY})
        if len(q) >= 3:
            response = requests.get(FEC_API_COMMITTEE_LOOKUP_ENDPOINT, params=params)
            if response.status_code != status.HTTP_404_NOT_FOUND:
                response.raise_for_status()

            json_results = response.json()
        else:
            json_results = {}

        fecfile_committees = list(
            self.get_queryset()
            .filter(Q(type="COM") & (Q(committee_id__icontains=q) | Q(name__icontains=q)))
            .exclude(id__in=exclude_ids)
            .values()
            .order_by("-committee_id")
        )
        fec_api_committees = json_results.get("results", [])
        fec_api_committees = [
            fac
            for fac in fec_api_committees
            if not any(fac["id"] == ffc["committee_id"] for ffc in fecfile_committees)
            and fac["id"] not in exclude_fec_ids
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
        exclude_ids = (
            request.GET.get("exclude_ids").split(",")
            if request.GET.get("exclude_ids")
            else []
        )

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
            .exclude(id__in=exclude_ids)
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
        exclude_ids = (
            request.GET.get("exclude_ids").split(",")
            if request.GET.get("exclude_ids")
            else []
        )

        fecfile_organizations = list(
            self.get_queryset()
            .filter(Q(type="ORG") & Q(name__icontains=q))
            .exclude(id__in=exclude_ids)
            .values()
            .order_by("-name")[:max_fecfile_results]
        )
        return_value = {"fecfile_organizations": fecfile_organizations}

        return JsonResponse(return_value)

    @action(detail=False)
    def get_contact_id(self, request):
        fec_id = request.GET.get("fec_id")
        if fec_id is None:
            return HttpResponseBadRequest()
        match = (
            self.get_queryset()
            .filter(Q(candidate_id=fec_id) | Q(committee_id=fec_id))
            .first()
        )
        return Response(match.id if match else "")

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().update(request, *args, **kwargs)

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

    @action(
        detail=False,
        methods=["post"],
        url_path="e2e-delete-all-contacts",
    )
    def e2e_delete_all_contacts(self, request):
        contacts = Contact.objects.filter(committee_account__committee_id="C99999999")
        contact_count = contacts.count()

        delete_all_contacts()
        delete_all_contacts("C99999998")
        return Response(f"Deleted {contact_count} Contacts")


class DeletedContactsViewSet(
    CommitteeOwnedViewMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = ContactSerializer
    pagination_class = ContactListPagination

    queryset = (
        Contact.all_objects.filter(deleted__isnull=False)
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

    @action(detail=False, methods=["post"])
    def restore(self, request):
        ids_to_restore = request.data
        contacts = self.queryset.filter(id__in=ids_to_restore)
        if len(ids_to_restore) != contacts.count():
            return Response(
                "Contact Ids are invalid",
                status=status.HTTP_400_BAD_REQUEST,
            )
        contacts.update(deleted=None)
        return Response(ids_to_restore)


def delete_all_contacts(committee_id="C99999999", log_method=logger.warn):
    contacts = Contact.objects.filter(committee_account__committee_id=committee_id)
    contact_count = contacts.count()

    log_method(f"Deleting Contacts for {committee_id}")
    log_method(f"Deleting Contacts: {contact_count}")

    contacts.delete()
