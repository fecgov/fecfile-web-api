from datetime import date
from rest_framework import serializers
from fecfile_validate import validate
from rest_framework import exceptions
from functools import reduce
import logging

logger = logging.getLogger(__name__)


class FecSchemaValidatorSerializerMixin(serializers.Serializer):
    """Serializer Mixin that runs fecfile_validate over incoming data

    Runs :py:function:`fecfile_validate.validate` over incoming data for the configured
    schema. Set the schema by defining :py:attribue:`schema_name` or
    overriding :py:function:`get_schema_name`p

    Attributes:
        schema_name (str): schema name that can be passed to
            :py:function:`fecfile_validate.validate` that will
            match a schema defined in the package

    """

    schema_name = None

    def get_schema_name(self, data):
        """Gets the schema name to retrieve the correct schema from fecfile_validate

        You need to either define `schema_name`, set the query parameter 'schema',
        or overide this function to provide the `validate` function with a schema

        Args:
            data: data being serialized.  May contain information needed to determine
                what schema you want to use

        Returns:
            string: schema name that can be passed to
            :py:function:`fecfile_validate.validate` that will
            match a schema defined in the package
        """
        request = self.context.get("request", None)
        if request and request.query_params.get("schema"):
            self.schema_name = request.query_params.get("schema")

        assert self.schema_name is not None, (
            f"'{self.__class__.__name__}' should either include a "
            "`schema_name` attribute, or override the `get_schema_name()` method."
        )
        return self.schema_name

    def get_validation_candidate(self, data):
        """Returns a copy of data where foreign key fields are replaced with the
        underlying foreign key field. Also dates and datetimes will be replaced
        with iso8601 strings

        Example:  the f3x table is related to the report code label table by the
            report code field.  DRF gives us the whole
            :py:class:`fecfiler.f3x_summaries.models.ReportCodeLabel` object.
            for validating purposes, we just want the report code.  With the
            foreign_key_fields mapping defined in Meta, we replace the foreign-key-
            related object with the key only.
        """
        validation_candidate = data.copy()
        for (foreign_key_field, actual_key) in self.get_foreign_key_fields().items():
            if hasattr(validation_candidate.get(foreign_key_field, {}), actual_key):
                validation_candidate[foreign_key_field] = getattr(
                    validation_candidate.get(foreign_key_field, {}), actual_key
                )

        for key, value in validation_candidate.items():
            if isinstance(value, date):
                validation_candidate[key] = value.isoformat()

        return validation_candidate

    def get_foreign_key_fields(self):
        """Returns a dictionary of foreign key fields"""
        meta = getattr(self, "Meta", None)
        foreign_key_fields = getattr(meta, "foreign_key_fields", None)
        return dict(foreign_key_fields) if foreign_key_fields else {}

    def validate(self, data):
        """Overrides Django Rest Framework's Serializer validate to validate with
        fecfile_validate rules.

        We need to translate the list of fecfile validation errors to a dictionary
            of ```path``` -> ```message``` to comply with DJR's validation error
            pattern
        """
        fields_to_validate = []
        request = self.context.get("request", None)
        if request:
            fields_to_validate_str = request.query_params.get("fields_to_validate")
            fields_to_validate = (
                fields_to_validate_str.split(",") if fields_to_validate_str else []
            )

        validation_result = validate.validate(
            self.get_schema_name(data),
            self.get_validation_candidate(data),
            fields_to_validate,
        )
        if validation_result.errors:

            def collect_error(all_errors, error):
                all_errors[error.path] = error.message
                return all_errors

            translated_errors = reduce(collect_error, validation_result.errors, {})
            logger.warning(
                f"{self.__class__.__name__}: Failed validation {list(translated_errors)}"
            )
            raise exceptions.ValidationError(translated_errors)
        return data
