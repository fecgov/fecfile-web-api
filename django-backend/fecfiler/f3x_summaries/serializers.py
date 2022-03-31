from .models import F3XSummary
from rest_framework import serializers, exceptions
from fecfile_validate import validate
from functools import reduce
import logging

logger = logging.getLogger(__name__)


class F3XSummarySerializer(serializers.ModelSerializer):
    def validate(self, data):
        """Overrides Django Rest Framework's Serializer validate to validate with
        fecfile_validate rules.

        We need to translate the list of fecfile validation errors to a dictionary
            of ```path``` -> ```message``` to comply with DJR's validation error
            pattern
        """
        validation_result = validate.validate("F3X", data)
        if validation_result.errors:

            def collect_error(all_errors, error):
                all_errors[error.path] = error.message
                return all_errors

            translated_errors = reduce(collect_error, validation_result.errors, {})
            logger.warning(
                f"F3X Summary: Failed validation for {list(translated_errors)}"
            )
            raise exceptions.ValidationError(translated_errors)
        return data

    class Meta:
        model = F3XSummary
        fields = [f.name for f in F3XSummary._meta.get_fields() if f.name != "deleted"]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
