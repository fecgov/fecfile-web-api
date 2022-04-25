from rest_framework import serializers, relations
from fecfile_validate import validate
from rest_framework import exceptions
from functools import reduce
import logging

logger = logging.getLogger(__name__)


class FecSchemaValidatorSerializer(serializers.ModelSerializer):
    schema_name = None

    def get_schema_name(self, data):
        assert self.schema_name is not None, (
            f"'{self.__class__.__name__}' should either include a `schema_name` attribute, "
            "or override the `get_schema_name()` method."
        )
        return self.schema_name

    def validate(self, data):
        """Overrides Django Rest Framework's Serializer validate to validate with
        fecfile_validate rules.

        We need to translate the list of fecfile validation errors to a dictionary
            of ```path``` -> ```message``` to comply with DJR's validation error
            pattern
        """
        validation_result = validate.validate(self.get_schema_name(data), data)
        if validation_result.errors:

            def collect_error(all_errors, error):
                all_errors[error.path] = error.message
                return all_errors

            translated_errors = reduce(collect_error, validation_result.errors, {})
            logger.warning(
                f"'{self.__class__.__name__}': Failed validation for {list(translated_errors)}"
            )
            raise exceptions.ValidationError(translated_errors)
        return data
