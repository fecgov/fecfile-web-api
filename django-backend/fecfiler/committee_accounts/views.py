from fecfiler.user.models import User
from rest_framework import filters, viewsets, mixins
from django.contrib.sessions.exceptions import SuspiciousSession
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CommitteeAccount, Membership
from .serializers import CommitteeAccountSerializer, CommitteeMembershipSerializer
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


class CommitteeMembershipViewSet(viewsets.ModelViewSet):
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

    @action(detail=True, methods=["get"])
    def members(self, request, pk):
        committee = self.get_object()
        queryset = Membership.objects.filter(committee_account=committee)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CommitteeMembershipSerializer(
                page, many=True
            )
            return self.get_paginated_response(serializer.data)

        serializer = CommitteeMembershipSerializer(
            queryset, many=True
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_member(self, request, pk):
        committee = self.get_object()
        queryset= Membership.objects.filter(committee_account=committee)

        email = request.data.get('email', None)
        role = request.data.get('role', None)

        missing_fields = []
        if email is None or len(email) == 0:
            missing_fields.append("email")

        if role is None:
            missing_fields.append("role")

        if len(missing_fields) > 0:
            return Response(f"Missing fields: {', '.join(missing_fields)}", status=400)

        if role not in Membership.CommitteeRole.choices:
            return Response(f"Invalid role", status=400)

        matching_users = User.objects.filter(email=email)
        if matching_users.count() > 0:
            for user in matching_users:
                added_member = committee.members.add(user)
                added_member.role = role
                added_member.save()
                logger.info(f"Added existing user {email} to committee {committee.committee_id}")
        else:
            Membership(
                committee_account=committee,
                pending_email=email,
                role=request.role
            ).save()
            logger.info(f"Added pending membership for email {email} for committee {committee.committee_id}")