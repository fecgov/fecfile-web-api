from fecfiler.user.models import User
from rest_framework import filters, viewsets, mixins
from django.contrib.sessions.exceptions import SuspiciousSession
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CommitteeAccount, Membership
from .serializers import CommitteeAccountSerializer, CommitteeMembershipSerializer
from django.db.models.fields import TextField
from django.db.models.functions import Coalesce, Concat
from django.db.models import Q, Value
import structlog

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
        committee_uuid = committee.id
        request.session["committee_uuid"] = str(committee_uuid)
        return Response("Committee activated")

    @action(detail=False, methods=["get"])
    def active(self, request):
        committee_uuid = request.session["committee_uuid"]
        committee = self.get_queryset().filter(id=committee_uuid).first()
        return Response(self.get_serializer(committee).data)


class CommitteeOwnedViewSet(viewsets.ModelViewSet):

    """ModelViewSet for models using CommitteeOwnedModel
    Inherit this view set to filter the queryset by the user's committee
    """

    def get_queryset(self):
        committee_uuid = self.request.session["committee_uuid"]
        committee = CommitteeAccount.objects.filter(id=committee_uuid).first()
        if not committee:
            raise SuspiciousSession("session has invalid committee_uuid")
        queryset = super().get_queryset()
        structlog.contextvars.bind_contextvars(
            committee_id=committee.committee_id, committee_uuid=committee.id
        )
        return queryset.filter(committee_account_id=committee.id)


class CommitteeMembershipViewSet(CommitteeOwnedViewSet):
    serializer_class = CommitteeMembershipSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "name",
        "email",
        "role",
        "is_active",
        "created"
    ]
    ordering = ["-created"]

    queryset = Membership.objects.all()

    def get_queryset(self):
        return super().get_queryset().annotate(
            name= Coalesce(
                Concat(
                    "user__last_name",
                    Value(", "),
                    "user__first_name",
                    output_field=TextField(),
                ),
                Value(''),
                output_field=TextField()
            ),
            email=Coalesce(
                "user__email",
                "pending_email",
                output_field=TextField()
            ),
            is_active=~Q(user=None)
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if 'page' in request.query_params:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="add-member", url_name="add_member")
    def add_member(self, request):
        committee_uuid = self.request.session["committee_uuid"]
        committee = CommitteeAccount.objects.filter(id=committee_uuid).first()

        email = request.data.get('email', None)
        role = request.data.get('role', None)

        # Check for necessary fields
        missing_fields = []
        if email is None or len(email) == 0:
            missing_fields.append("email")

        if role is None:
            missing_fields.append("role")

        if len(missing_fields) > 0:
            return Response(f"Missing fields: {', '.join(missing_fields)}", status=400)

        # Check for valid role
        choiceOf = False
        for choice in Membership.CommitteeRole.choices:
            if role in choice:
                choiceOf = True
                break
        if not choiceOf:
            return Response(f"Invalid role", status=400)

        # Check for pre-existing membership
        matching_memberships = self.get_queryset().filter(Q(pending_email=email) | Q(user__email=email))
        if matching_memberships.count() > 0:
            return Response(f"This email is already a member", status=400)

        # Create new membership
        new_member = None
        matching_users = User.objects.filter(email=email)
        if matching_users.count() > 0:
            for user in matching_users:
                new_member = committee.members.add(user)
                new_member.role = role
                logger.info(f"Added existing user {email} to committee {committee.committee_id}")
        else:
            new_member = Membership(
                committee_account=committee,
                pending_email=email,
                role=role
            )
            logger.info(f"Added pending membership for email {email} for committee {committee.committee_id}")

        new_member.save()
        return Response(CommitteeMembershipSerializer(new_member).data, status=200)