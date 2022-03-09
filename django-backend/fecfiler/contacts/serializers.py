from .models import Contact
from rest_framework import serializers


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id',
            'deleted',
            'type',
            'candidate_id',
            'committee_id',
            'name',
            'last_name',
            'first_name',
            'middle_name',
            'prefix',
            'suffix',
            'street_1',
            'street_2',
            'city',
            'state',
            'zip',
            'employer',
            'occupation',
            'candidate_office',
            'candidate_state',
            'candidate_district',
            'telephone',
            'country',
            'created',
            'updated',
        ]
