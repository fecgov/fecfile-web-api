from django.db import transaction
from django.db.models import TextField, Value
from django.db.models.functions import Coalesce, Concat
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.contacts.models import Contact
from fecfiler.contacts.serializers import ContactSerializer
from fecfiler.f3x_summaries.views import ReportViewMixin
from rest_framework import filters, status
from rest_framework.response import Response

from .models import SchATransaction
from .serializers import SchATransactionParentSerializer

import logging

logger = logging.getLogger(__name__)


class SchATransactionViewSet(CommitteeOwnedViewSet, ReportViewMixin):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limmited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    queryset = (
        SchATransaction.objects.select_related("parent_transaction")
        .alias(
            contributor_name=Coalesce(
                "contributor_organization_name",
                Concat(
                    "contributor_last_name",
                    Value(", "),
                    "contributor_first_name",
                    output_field=TextField(),
                ),
            )
        )
        .all()
    )

    serializer_class = SchATransactionParentSerializer
    permission_classes = []
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "id",
        "transaction_type_identifier",
        "contributor_name",
        "contribution_date",
        "memo_code",
        "contribution_amount",
    ]
    ordering = ["-id"]

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            response = self.create_or_update_contact(request)
            if response:
                return response
            return super().create(request, args, kwargs)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            response = self.create_or_update_contact(request)
            if response:
                return response
            return super().update(request, args, kwargs)

    def create_or_update_contact(self, request):
        request_transaction = request.data.get("transaction")
        if not request_transaction:
            return Response(
                "No transaction provided", status=status.HTTP_400_BAD_REQUEST
            )
        request_contact = request.data.get("contact")
        request_transaction_contact_id = request_transaction.get("contact_id")
        if not request_transaction_contact_id:
            if not request_contact:
                return Response(
                    "No contact provided with no transaction contact id",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            contact_serializer = ContactSerializer(
                data=request_contact, context={"request": request}
            )
            if not contact_serializer.is_valid():
                return Response(
                    contact_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            contact = Contact(**contact_serializer.validated_data)
            contact.save()
            request_transaction["contact_id"] = contact.id
        else:
            contact = Contact.objects.get(id=request_transaction_contact_id)
            changes = self.update_contact_for_transaction(contact, request_transaction)
            if changes:
                contact.save()
        request.data.clear()
        request.data.update(request_transaction)

    def update_contact_for_transaction(self, contact: Contact, transaction: dict):
        changes = False
        if contact and transaction:
            if (contact.type == Contact.ContactType.INDIVIDUAL) and (
                transaction["entity_type"] == "IND"
            ):
                if self.update_ind_contact_for_transaction(contact, transaction):
                    changes = True
            elif (contact.type == Contact.ContactType.COMMITTEE) and (
                transaction["entity_type"] == "COM"
            ):
                if self.update_com_contact_for_transaction(contact, transaction):
                    changes = True
            elif (contact.type == Contact.ContactType.ORGANIZATION) and (
                transaction["entity_type"] == "ORG"
            ):
                if self.update_org_contact_for_transaction(contact, transaction):
                    changes = True
            if self.update_contact_for_transaction_shared_fields(contact, transaction):
                changes = True
        return changes

    def update_ind_contact_for_transaction(self, contact: Contact, transaction: dict):
        changes = False
        contributor_last_name = transaction.get("contributor_last_name")
        if contact.last_name != contributor_last_name:
            contact.last_name = contributor_last_name
            changes = True
        contributor_first_name = transaction.get("contributor_first_name")
        if contact.first_name != contributor_first_name:
            contact.first_name = contributor_first_name
            changes = True
        contributor_middle_name = transaction.get("contributor_middle_name")
        if contact.middle_name != contributor_middle_name:
            contact.middle_name = contributor_middle_name
            changes = True
        contributor_prefix = transaction.get("contributor_prefix")
        if contact.prefix != contributor_prefix:
            contact.prefix = contributor_prefix
            changes = True
        contributor_suffix = transaction.get("contributor_suffix")
        if contact.suffix != contributor_suffix:
            contact.suffix = contributor_suffix
            changes = True
        contributor_employer = transaction.get("contributor_employer")
        if contact.employer != contributor_employer:
            contact.employer = contributor_employer
            changes = True
        contributor_occupation = transaction.get("contributor_occupation")
        if contact.occupation != contributor_occupation:
            contact.occupation = contributor_occupation
            changes = True
        return changes

    def update_com_contact_for_transaction(self, contact: Contact, transaction: dict):
        changes = False
        donor_committee_fec_id = transaction.get("donor_committee_fec_id")
        if contact.committee_id != donor_committee_fec_id:
            contact.committee_id = donor_committee_fec_id
            changes = True
        contributor_organization_name = transaction.get("contributor_organization_name")
        if contact.name != contributor_organization_name:
            contact.name = contributor_organization_name
            changes = True
        return changes

    def update_org_contact_for_transaction(self, contact: Contact, transaction: dict):
        changes = False
        contributor_organization_name = transaction.get("contributor_organization_name")
        if contact.name != contributor_organization_name:
            contact.name = contributor_organization_name
            changes = True
        return changes

    def update_contact_for_transaction_shared_fields(
        self, contact: Contact, transaction: dict
    ):
        changes = False
        contributor_street_1 = transaction.get("contributor_street_1")
        if contact.street_1 != contributor_street_1:
            contact.street_1 = contributor_street_1
            changes = True
        contributor_street_2 = transaction.get("contributor_street_2")
        if contact.street_2 != contributor_street_2:
            contact.street_2 = contributor_street_2
            changes = True
        contributor_city = transaction.get("contributor_city")
        if contact.city != contributor_city:
            contact.city = contributor_city
            changes = True
        contributor_zip = transaction.get("contributor_zip")
        if contact.zip != contributor_zip:
            contact.zip = contributor_zip
            changes = True
        return changes
