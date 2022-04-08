from .models import Contact
from fecfiler.authentication.models import Account
from fecfiler.committee_accounts.models import CommitteeAccount
from rest_framework import serializers, exceptions, relations
from fecfile_validate import validate
from functools import reduce
import logging

logger = logging.getLogger(__name__)


class ContactSerializer(serializers.ModelSerializer):
    committee_account_id = relations.PrimaryKeyRelatedField(
        queryset=CommitteeAccount.objects.all()
    )

    def validate(self, data):
        """Overrides Django Rest Framework's Serializer validate to validate with
        fecfile_validate rules.

        We need to translate the list of fecfile validation errors to a dictionary
            of ```path``` -> ```message``` to comply with DJR's validation error
            pattern
        """

        contact_value = dict(
            COM="Committee",
            IND="Individual",
            ORG="Organization",
            CAN="Candidate",
        )
        schema_name = f"Contact_{contact_value[data.get('type', None)]}"
        validation_result = validate.validate(schema_name, data)
        if validation_result.errors:

            def collect_error(all_errors, error):
                all_errors[error.path] = error.message
                return all_errors

            translated_errors = reduce(collect_error, validation_result.errors, {})
            logger.warning(f"Contact: Failed validation for {list(translated_errors)}")
            raise exceptions.ValidationError(translated_errors)
        return data

    def to_internal_value(self, data):
        request = self.context["request"]
        user = request.user
        committee = CommitteeAccount.objects.get(committee_id=user.cmtee_id)
        data["committee_account_id"] = committee.id
        return super().to_internal_value(data)

    class Meta:
        model = Contact
        fields = [
            f.name for f in Contact._meta.get_fields() if f.name not in ["deleted"]
        ]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
