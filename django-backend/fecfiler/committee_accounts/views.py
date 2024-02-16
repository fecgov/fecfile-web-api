from rest_framework import viewsets, mixins
from django.contrib.sessions.exceptions import SuspiciousSession
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CommitteeAccount
from .serializers import CommitteeAccountSerializer, CommitteeMemberSerializer
import structlog
from django.http import HttpResponse

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
    
    @action(detail=True, methods=["delete"])
    def remove_member(request, committee_id, member_email):
        committee_uuid = request.session["committee_uuid"]
        committee = CommitteeAccount.objects.filter(id=committee_uuid).first()
        member = committee.members.filter(email=member_email).first()
        member.delete()
        return HttpResponse('Member removed')


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
