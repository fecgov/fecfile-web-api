from .models import SchATransaction
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from rest_framework import exceptions
from fecfile_validate import validate
from functools import reduce
import logging

logger = logging.getLogger(__name__)


class SchATransactionSerializer(CommitteeOwnedSerializer):
    def validate(self, data):
        """Overrides Django Rest Framework's Serializer validate to validate with
        fecfile_validate rules.

        We need to translate the list of fecfile validation errors to a dictionary
            of ```path``` -> ```message``` to comply with DJR's validation error
            pattern
        """
        validation_result = validate.validate("SchA", data)
        if validation_result.errors:

            def collect_error(all_errors, error):
                all_errors[error.path] = error.message
                return all_errors

            translated_errors = reduce(collect_error, validation_result.errors, {})
            logger.warning(
                f"Schedule A: Failed validation for {list(translated_errors)}"
            )
            raise exceptions.ValidationError(translated_errors)
        return data

    class Meta:
        model = SchATransaction
        fields = [
            f.name for f in SchATransaction._meta.get_fields() if f.name != "deleted"
        ]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
