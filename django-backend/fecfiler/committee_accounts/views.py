from uuid import UUID
from fecfiler.user.models import User
from rest_framework import filters, viewsets, mixins, pagination, status
from django.contrib.sessions.exceptions import SuspiciousSession
from rest_framework.decorators import action
from rest_framework.response import Response
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.committee_accounts.utils import (
    check_can_create_committee_account,
    create_committee_account,
    get_committee_account_data,
)
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import CommitteeAccountSerializer, CommitteeMembershipSerializer
from django.db.models.fields import TextField
from django.db.models.functions import Coalesce, Concat
from django.db.models import Q, Value
import structlog

logger = structlog.get_logger(__name__)


class CommitteeMemberListPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class CommitteePagination(pagination.PageNumberPagination):
    page_size = 100


class CommitteeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CommitteeAccountSerializer
    pagination_class = CommitteePagination

    def get_queryset(self):
        user = self.request.user
        return CommitteeAccount.objects.filter(members=user)

    @extend_schema(
        request=CommitteeAccountSerializer,
        responses=CommitteeAccountSerializer,
        parameters=[
            OpenApiParameter(name="id", type=str, location=OpenApiParameter.PATH)
        ],
    )
    @action(detail=True, methods=["post"])
    def activate(self, request, pk):
        committee = self.get_object()
        if not committee:
            return Response("Committee could not be activated", status=403)
        request.session["committee_id"] = str(committee.committee_id)
        request.session["committee_uuid"] = str(committee.id)

        return Response("Committee activated")

    @action(detail=False, methods=["get"])
    def active(self, request):
        committee_uuid = request.session["committee_uuid"]
        committee = self.get_queryset().filter(id=committee_uuid).first()
        return Response(self.get_serializer(committee).data)

    @action(detail=False, methods=["post"])
    def create_account(self, request):
        committee_id = request.data.get("committee_id")
        if not committee_id:
            raise Exception("no committee_id provided")
        account = create_committee_account(committee_id, request.user)

        return Response(
            self.add_committee_account_data(CommitteeAccountSerializer(account).data)
        )

    @action(detail=False, methods=["get"], url_path="get-available-committee")
    def get_available_committee(self, request):
        committee_id = request.query_params.get("committee_id")
        committee = get_committee_account_data(committee_id)
        if check_can_create_committee_account(committee_id, request.user):
            return Response(committee)
        response = {"message": "No available committee found."}
        return Response(response, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        response = super(CommitteeViewSet, self).list(request, *args, **kwargs)
        response.data["results"] = [
            self.add_committee_account_data(committee_account)
            for committee_account in response.data["results"]
        ]
        return response

    def add_committee_account_data(self, committee_account):
        committee_data = get_committee_account_data(committee_account["committee_id"])
        return {**committee_account, **(committee_data or {})}


class CommitteeOwnedViewMixin(viewsets.GenericViewSet):
    """ModelViewSet for models using CommitteeOwnedModel
    Inherit this view set to filter the queryset by the user's committee
    """

    def get_queryset(self):
        committee_uuid = self.get_committee_uuid()
        committee_id = self.get_committee_id()
        structlog.contextvars.bind_contextvars(
            committee_id=committee_id, committee_uuid=committee_uuid
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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if "page" in request.query_params:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CommitteeMembershipViewSet(CommitteeOwnedViewMixin, viewsets.ModelViewSet):
    serializer_class = CommitteeMembershipSerializer
    pagination_class = CommitteeMemberListPagination
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
                email=Coalesce("user__email", "pending_email", output_field=TextField()),
                is_active=~Q(user=None),
            )
        )

    @action(detail=False, methods=["post"], url_path="add-member", url_name="add_member")
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
            Q(pending_email__iexact=email) | Q(user__email__iexact=email)
        )
        if matching_memberships.count() > 0:
            return Response(
                "This email is taken by an existing membership to this committee",
                status=400,
            )

        # Create new membership
        user = User.objects.filter(email__iexact=email).first()

        membership_args = {
            "committee_account": committee,
            "role": role,
            "user": user,
        } | (
            {"pending_email": email} if user is None else {}
        )  # Add pending email to args only if there is no user

        new_member = Membership(**membership_args)
        new_member.save()

        action = f'existing user {user.id} to' if user else "pending membership for"
        logger.info(
            f'User {request.user.id} added {action} committee {committee} as {role}'
        )

        return Response(CommitteeMembershipSerializer(new_member).data, status=200)

    @action(
        detail=True,
        methods=["delete"],
        url_path="remove-member",
        url_name="remove_member",
    )
    def remove_member(self, request, pk: UUID):
        member: Membership = self.get_object()
        committee_id = request.session["committee_id"]
        if member.user == request.user:
            logger.info(
                f"{request.user.id} attempted to remove themselves "
                f"from committee {committee_id}"
            )
            return Response(
                {"error": "You cannot remove yourself from the committee."}, status=400
            )

        # Call the model's delete method (which already checks the admin count)
        try:
            member.delete()
            logger.info(
                f"{request.user.id} removed {member.id} "
                f"from committee {committee_id}"
            )
            return Response({"success": "Membership removed."})
        except ValidationError as e:
            logger.info(f"{str(e)}")
            return Response({"error": str(e)}, status=400)

    def update(self, request, *args, **kwargs):
        committee_uuid = request.session["committee_uuid"]
        role = (
            Membership.objects.filter(
                user=request.user, committee_account_id=committee_uuid
            )
            .values_list("role", flat=True)
            .first()
        )
        if role != Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR:
            return Response(
                "You don't have permission to perform this action.",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        existing_member = self.get_object()
        user_id = existing_member.id
        committee = existing_member.committee_account
        # member updates
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_role = request.data.get("role")
        logger.info(
            f'Updating role for User "{user_id}" in committee {committee} to {new_role}'
        )
        return super().update(request, *args, **kwargs)
