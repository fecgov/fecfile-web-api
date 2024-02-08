from rest_framework import viewsets
from fecfiler.committee_accounts.models import CommitteeAccount
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CommitteeAccount
from .serializers import CommitteeAccountSerializer, CommitteeMemberSerializer
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


class CommitteeOwnedViewMixin(viewsets.GenericViewSet):

    """ModelViewSet for models using CommitteeOwnedModel
    Inherit this view set to filter the queryset by the user's committee
    """

    def get_queryset(self):
        committee = self.request.user.committeeaccount_set.first()
        queryset = super().get_queryset()
        structlog.contextvars.bind_contextvars(
            committee_id=committee.committee_id, committee_uuid=committee.id
        )
        return queryset.filter(committee_account_id=committee.id)

    def get_committee(self):
        committee_id = self.request.user.cmtee_id
        return CommitteeAccount.objects.get(committee_id=committee_id)
