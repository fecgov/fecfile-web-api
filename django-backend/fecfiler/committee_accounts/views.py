from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CommitteeAccount
from .serializers import CommitteeAccountSerializer, CommitteeMemberSerializer
from fecfiler.settings import FFAPI_COMMITTEE_UUID_COOKIE_NAME, FFAPI_COOKIE_DOMAIN
import structlog

logger = structlog.get_logger(__name__)


class CommitteeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CommitteeAccountSerializer

    def get_queryset(self):
        user = self.request.user
        return CommitteeAccount.objects.filter(members=user)

    @action(detail=True, methods=["get"])
    def users(self, request, pk):
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
    def activate_committee(self, request):
        committee = self.get_object()
        committee_uuid = committee.id
        response = Response("Committee activated")
        response.set_cookie(
            FFAPI_COMMITTEE_UUID_COOKIE_NAME,
            committee_uuid,
            domain=FFAPI_COOKIE_DOMAIN,
            secure=True,
        )
        return response


class CommitteeOwnedViewSet(viewsets.ModelViewSet):
    """ModelViewSet for models using CommitteeOwnedModel
    Inherit this view set to filter the queryset by the user's committee
    """

    def get_queryset(self):
        committee_id = self.request.user.committeeaccount_set.first().id
        queryset = super().get_queryset()
        return queryset.filter(committee_account_id=committee_id)
