from uuid import UUID
from fecfiler.user.models import User
from rest_framework import filters, viewsets, mixins
from django.contrib.sessions.exceptions import SuspiciousSession
from fecfiler.transactions.models import (
    Transaction,
    get_committee_view_name,
    get_read_model,
)
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CommitteeAccount, Membership
from fecfiler.openfec.views import retrieve_recent_f1
from fecfiler.mock_openfec.mock_endpoints import recent_f1
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.settings import MOCK_OPENFEC_REDIS_URL
import requests
from .serializers import CommitteeAccountSerializer, CommitteeMembershipSerializer
from django.db.models.fields import TextField
from django.db.models.functions import Coalesce, Concat
from django.db.models import Q, Value
from django.db import connection
import structlog
from django.http import HttpResponse

logger = structlog.get_logger(__name__)


class CommitteeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CommitteeAccountSerializer

    def get_queryset(self):
        user = self.request.user
        return CommitteeAccount.objects.filter(members=user)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk):
        committee = self.get_object()
        if not committee:
            return Response("Committee could not be activated", status=403)
        request.session["committee_id"] = str(committee.committee_id)
        request.session["committee_uuid"] = str(committee.id)
        """ create view if it doesn't exist """
        get_read_model(committee.id)
        return Response("Committee activated")

    @action(detail=False, methods=["get"])
    def active(self, request):
        committee_uuid = request.session["committee_uuid"]
        committee = self.get_queryset().filter(id=committee_uuid).first()
        return Response(self.get_serializer(committee).data)

    @action(detail=False, methods=["post"])
    def register(self, request):
        committee_id = request.data.get("committee_id")
        if not committee_id:
            raise Exception("no committee_id provided")
        account = register_committee(committee_id, request.user)

        return Response(CommitteeAccountSerializer(account).data)


class CommitteeOwnedViewMixin(viewsets.GenericViewSet):
    """ModelViewSet for models using CommitteeOwnedModel
    Inherit this view set to filter the queryset by the user's committee
    """

    def get_queryset(self):
        committee_uuid = self.get_committee_uuid()
        committee_id = self.get_committee_id()
        structlog.contextvars.bind_contextvars(
            committee_id=committee_id, committee_uuid=committee_id
        )
        return super().get_queryset().filter(committee_account_id=committee_uuid)

    def get_committee_uuid(self):
        committee_uuid = self.request.session["committee_uuid"]
        if not committee_uuid:
            raise SuspiciousSession("session has invalid committee_uuid")
        return committee_uuid

    def get_committee_id(self):
        committee_id = self.request.session["committee_id"]
        if not committee_id:
            raise SuspiciousSession("session has invalid committee_id")
        return committee_id


class CommitteeMembershipViewSet(CommitteeOwnedViewMixin, viewsets.ModelViewSet):
    serializer_class = CommitteeMembershipSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["name", "email", "role", "is_active", "created"]
    ordering = ["-created"]

    queryset = Membership.objects.all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                name=Coalesce(
                    Concat(
                        "user__last_name",
                        Value(", "),
                        "user__first_name",
                        output_field=TextField(),
                    ),
                    Value(""),
                    output_field=TextField(),
                ),
                email=Coalesce(
                    "user__email", "pending_email", output_field=TextField()
                ),
                is_active=~Q(user=None),
            )
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if "page" in request.query_params:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False, methods=["post"], url_path="add-member", url_name="add_member"
    )
    def add_member(self, request):
        committee_uuid = self.request.session["committee_uuid"]
        committee = CommitteeAccount.objects.filter(id=committee_uuid).first()

        email = request.data.get("email", None)
        role = request.data.get("role", None)

        # Check for necessary fields
        missing_fields = []
        if email is None or len(email) == 0:
            missing_fields.append("email")

        if role is None:
            missing_fields.append("role")

        if len(missing_fields) > 0:
            return Response(f"Missing fields: {', '.join(missing_fields)}", status=400)

        # Check for valid role
        choice_of = False
        for choice in Membership.CommitteeRole.choices:
            if role in choice:
                choice_of = True
                break
        if not choice_of:
            return Response("Invalid role", status=400)

        # Check for pre-existing membership
        matching_memberships = self.get_queryset().filter(
            Q(pending_email=email) | Q(user__email=email)
        )
        if matching_memberships.count() > 0:
            return Response(
                "This email is taken by an existing membership to this committee",
                status=400,
            )

        # Create new membership
        user = User.objects.filter(email=email).first()

        membership_args = {
            "committee_account": committee,
            "role": role,
            "user": user,
        } | (
            {"pending_email": email} if user is None else {}
        )  # Add pending email to args only if there is no user

        new_member = Membership(**membership_args)
        new_member.save()

        member_type = "existing user" if user else "pending membership for"
        logger.info(f'Added {member_type} "{email}" to committee {committee}')

        return Response(CommitteeMembershipSerializer(new_member).data, status=200)

    @action(
        detail=True,
        methods=["delete"],
        url_path="remove-member",
        url_name="remove_member",
    )
    def remove_member(self, request, pk: UUID):
        member = self.get_object()
        member.delete()
        return HttpResponse("Member removed")


def register_committee(committee_id, user):
    email = user.email

    if MOCK_OPENFEC_REDIS_URL:
        f1 = recent_f1(committee_id)
        f1_email = (f1 or {}).get("email")
    else:
        f1 = retrieve_recent_f1(committee_id)
        dot_fec_url = (f1 or {}).get("fec_url")
        if dot_fec_url:
            response = requests.get(
                dot_fec_url,
                headers={"User-Agent": "fecfile-api"},
            )
            dot_fec_content = response.content.decode("utf-8")
            f1_line = dot_fec_content.split("\n")[1]
            f1_email = f1_line.split(FS_STR)[11]

    failure_reason = None
    if f1_email != email:
        failure_reason = f"Email {email} does not match committee email"

    existing_account = CommitteeAccount.objects.filter(
        committee_id=committee_id
    ).first()
    if existing_account:
        failure_reason = f"Committee {committee_id} already registered"

    if failure_reason:
        logger.error(f"Failure to register committee: {failure_reason}")
        raise ValidationError("could not register committee")

    account = CommitteeAccount.objects.create(committee_id=committee_id)
    Membership.objects.create(
        committee_account=account,
        user=user,
        role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
    )

    create_committee_view(account.id)
    return account


def create_committee_view(committee_uuid):
    view_name = get_committee_view_name(committee_uuid)
    with connection.cursor() as cursor:
        sql, params = (
            Transaction.objects.transaction_view()
            .filter(committee_account_id=committee_uuid)
            .query.sql_with_params()
        )
        definition = cursor.mogrify(sql, params).decode("utf-8")
        cursor.execute(
            f"DROP VIEW IF EXISTS {view_name};"
            f"CREATE  VIEW {view_name} as {definition}"
        )
