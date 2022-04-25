from rest_framework import serializers, relations
from fecfile_validate import validate
from rest_framework import exceptions
from functools import reduce
import logging

logger = logging.getLogger(__name__)


class FecSchemaValidatorSerializerMixin(serializers.ModelSerializer):
    """Serializer Mixin that runs fecfile_validate over incoming data

    Runs :py:function:`fecfile_validate.validate` over incoming data for the configured
    schema. Set the schema by defining :py:attribue:`schema_name` or
    overriding :py:function:`get_schema_name`

    Attributes:
        schema_name (str): schema name that can be passed to :py:function:`fecfile_validate.validate`
            that will match a schema defined in the package

    """

    def __init__(self):
        self.schema_name = None

    def get_schema_name(self, data):
        """Gets the schema name to retrieve the correct schema from fecfile_validate

        You need to either define `schema_name` or overide this function to provide the
        `validate` function with a schema

        Args:
            data: data being serialized.  May contain information needed to determine
                what schema you want to use

        Returns:
            string: schema name that can be passed to :py:function:`fecfile_validate.validate`
            that will match a schema defined in the package
        """
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
