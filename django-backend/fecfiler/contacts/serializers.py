from .models import Contact
from rest_framework import serializers, exceptions
from fecfile_validate import validate
from functools import reduce


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    def validate(self, data):
        """Overrides Django Rest Framework's Serializer validate to validate with
        fecfile_validate rules.

        We need to translate the list of fecfile validation errors to a dictionary
            of ```path``` -> ```message``` to comply with DJR's validation error
            pattern
        """
        schema_name = f"Contact_{data.get('type', None)}"
        validation_result = validate.validate(schema_name, data)
        if validation_result.errors:

            def collect_error(all_errors, error):
                all_errors[error.path] = error.message
                return all_errors

            translated_errors = reduce(collect_error, validation_result.errors, {})
            raise exceptions.ValidationError(translated_errors)
        return data

    class Meta:
        model = Contact
        fields = [
            "id",
            "deleted",
            "type",
            "candidate_id",
            "committee_id",
            "name",
            "last_name",
            "first_name",
            "middle_name",
            "prefix",
            "suffix",
            "street_1",
            "street_2",
            "city",
            "state",
            "zip",
            "employer",
            "occupation",
            "candidate_office",
            "candidate_state",
            "candidate_district",
            "telephone",
            "country",
            "created",
            "updated",
        ]
