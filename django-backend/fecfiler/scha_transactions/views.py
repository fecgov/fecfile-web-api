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
from .serializers import SchATransactionSerializer


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
    """QuerySet: all schedule a transactions with an aditional contributor_name field"""

    serializer_class = SchATransactionSerializer
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
            return self.create_or_update_contact(request, args, kwargs)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            return self.create_or_update_contact(request, args, kwargs)

    def create_or_update_contact(self, request, *args, **kwargs):
        scha_tran_serializer = SchATransactionSerializer(
            data=request.data["transaction"], context={"request": request})
        if not scha_tran_serializer.is_valid():
            return Response(
                scha_tran_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        scha_tran = SchATransaction(**scha_tran_serializer.validated_data)
        tran_contact = scha_tran.contact
        contact_id = None
        if (tran_contact):
            contact_id = tran_contact.id
        if not contact_id:
            contact_serializer = ContactSerializer(
                data=request.data["contact"], context={"request": request})
            if not contact_serializer.is_valid():
                return Response(
                    contact_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            contact = Contact(**contact_serializer.validated_data)
        else:
            contact = Contact.objects.get(id=contact_id)
        self.update_contact_for_transaction(contact, scha_tran)
        scha_tran_serializer.validated_data["contact_id"] = contact.id
        scha_tran_serializer.save()

        headers = self.get_success_headers(scha_tran_serializer.data)
        return Response(
            scha_tran_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update_contact_for_transaction(
            self, contact: Contact, scha_tran: SchATransaction):
        if contact and scha_tran:
            if ((contact.type == Contact.ContactType.INDIVIDUAL)
                    and (scha_tran.entity_type == "IND")):
                if (contact.last_name != scha_tran.contributor_last_name):
                    contact.last_name = scha_tran.contributor_last_name
                if (contact.first_name != scha_tran.contributor_first_name):
                    contact.first_name = scha_tran.contributor_first_name
                if (contact.middle_name != scha_tran.contributor_middle_name):
                    contact.middle_name = scha_tran.contributor_middle_name
                if (contact.prefix != scha_tran.contributor_prefix):
                    contact.prefix = scha_tran.contributor_prefix
                if (contact.suffix != scha_tran.contributor_suffix):
                    contact.suffix = scha_tran.contributor_suffix
                if (contact.employer != scha_tran.contributor_employer):
                    contact.employer = scha_tran.contributor_employer
                if (contact.occupation != scha_tran.contributor_occupation):
                    contact.occupation = scha_tran.contributor_occupation
            elif ((contact.type == Contact.ContactType.COMMITTEE)
                  and (scha_tran.entity_type == "COM")):
                if (contact.committee_id != scha_tran.donor_committee_fec_id):
                    contact.committee_id = scha_tran.donor_committee_fec_id
                if (contact.name != scha_tran.contributor_organization_name):
                    contact.name = scha_tran.contributor_organization_name
            elif ((contact.type == Contact.ContactType.ORGANIZATION)
                  and (scha_tran.entity_type == "ORG")):
                if (contact.name != scha_tran.contributor_organization_name):
                    contact.name = scha_tran.contributor_organization_name
            if (contact.street_1 != scha_tran.contributor_street_1):
                contact.street_1 = scha_tran.contributor_street_1
            if (contact.street_2 != scha_tran.contributor_street_2):
                contact.street_2 = scha_tran.contributor_street_2
            if (contact.city != scha_tran.contributor_city):
                contact.city = scha_tran.contributor_city
            if (contact.zip != scha_tran.contributor_zip):
                contact.zip = scha_tran.contributor_zip
            contact.save()
