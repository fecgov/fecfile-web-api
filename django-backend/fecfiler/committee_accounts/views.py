from rest_framework import viewsets, mixins
from django.contrib.sessions.exceptions import SuspiciousSession
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CommitteeAccount, Membership
from .serializers import CommitteeAccountSerializer, CommitteeMemberSerializer
from fecfiler.openfec.views import retrieve_recent_f1
from fecfiler.mock_openfec.mock_endpoints import recent_f1
from fecfiler.settings import MOCK_OPENFEC_REDIS_URL
import structlog

logger = structlog.get_logger(__name__)


class CommitteeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CommitteeAccountSerializer

    def get_queryset(self):
        user = self.request.user
        return CommitteeAccount.objects.filter(members=user)

    @action(detail=True, methods=["get"])
    def members(self, request, pk):
        committee = self.get_object()
        serializer_context = {"committee_id": committee.id}
        queryset = self.filter_queryset(committee.members.all())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CommitteeMemberSerializer(
                page, many=True, context=serializer_context
            )
            return self.get_paginated_response(serializer.data)

        serializer = CommitteeMemberSerializer(
            queryset, many=True, context=serializer_context
        )
        return Response(serializer.data)

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

    @action(detail=False, methods=["post"])
    def register(self, request):
        email = request.user.email
        committee_id = request.data.get("committee_id")
        if not committee_id:
            raise Exception("no committee_id provided")
        if MOCK_OPENFEC_REDIS_URL:
            f1 = recent_f1(committee_id)
        else:
            f1 = retrieve_recent_f1(committee_id)
        existing_account = CommitteeAccount.objects.filter(
            committee_id=committee_id
        ).first()
        if existing_account or not f1 or f1.get("email") != email:
            raise Exception("could not register committee")
        account = CommitteeAccount.objects.create(committee_id=committee_id)
        Membership.objects.create(
            committee_account=account,
            user=request.user,
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
        )
        return Response(account)


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
