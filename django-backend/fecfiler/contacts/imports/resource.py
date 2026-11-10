from django.core.exceptions import ValidationError
from django.db import transaction
from import_export_extensions.resources import CeleryModelResource
from rest_framework.exceptions import ValidationError as SerializerValidationError

from fecfiler.committee_accounts.models import Membership
from fecfiler.contacts.models import Contact
from .format import CONTACT_COLUMNS, ContactsCSV
from .serializers import ContactImportRowSerializer

PERSON = {
    "first_name",
    "last_name",
    "middle_name",
    "prefix",
    "suffix",
    "employer",
    "occupation",
}
COMMON = {"type", "street_1", "street_2", "city", "state", "zip", "country", "telephone"}
TYPE_FIELDS = {
    "IND": COMMON | PERSON,
    "CAN": COMMON
    | PERSON
    | {"candidate_id", "candidate_office", "candidate_state", "candidate_district"},
    "COM": COMMON | {"name", "committee_id"},
    "ORG": COMMON | {"name"},
}


class ContactImportResource(CeleryModelResource):
    SUPPORTED_FORMATS = [ContactsCSV]

    class Meta:
        model = Contact
        fields = CONTACT_COLUMNS
        export_order = CONTACT_COLUMNS
        import_id_fields = []
        force_init_instance = True
        store_instance = True
        use_transactions = True

    def __init__(self, committee_id=None, user_id=None, **kwargs):
        self.committee_id = committee_id
        self.user_id = user_id
        super().__init__(**kwargs)

    def _import_data(self, dataset, **kwargs):
        # Enforce atomicity even if a caller requests partial import or no transaction.
        kwargs.update(
            use_transactions=True, rollback_on_validation_errors=True, force_import=False
        )
        with transaction.atomic():
            membership = (
                Membership.objects.select_for_update()
                .filter(
                    committee_account_id=self.committee_id,
                    committee_account__disabled__isnull=True,
                    committee_account__deleted__isnull=True,
                    user_id=self.user_id,
                    user__is_active=True,
                    role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
                )
                .first()
            )
            if membership is None:
                raise ValueError(
                    "The import creator must remain an administrator of this committee."
                )
            return super()._import_data(dataset, **kwargs)

    def before_import_row(self, row, **kwargs):
        values = {
            key: value.strip()
            for key, value in row.items()
            if value is not None and value.strip()
        }
        contact_type = values.get("type")
        if contact_type in TYPE_FIELDS:
            irrelevant = set(values) - TYPE_FIELDS[contact_type]
            if irrelevant:
                raise ValidationError(
                    {
                        key: [f"Leave this field blank for {contact_type} contacts."]
                        for key in irrelevant
                    }
                )
        serializer = ContactImportRowSerializer(data=values)
        try:
            serializer.is_valid(raise_exception=True)
        except SerializerValidationError as error:
            raise ValidationError(
                {
                    key: [
                        str(message)
                        for message in (
                            messages if isinstance(messages, list) else [messages]
                        )
                    ]
                    for key, messages in error.detail.items()
                }
            )
        row.update({key: serializer.validated_data.get(key) for key in CONTACT_COLUMNS})

    def import_instance(self, instance, row, **kwargs):
        # All CSV values are text; preserve absent optional values as null.
        for key in CONTACT_COLUMNS:
            setattr(instance, key, row.get(key))

    def before_save_instance(self, instance, row, **kwargs):
        instance.committee_account_id = self.committee_id
