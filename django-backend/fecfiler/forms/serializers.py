from rest_framework import serializers
from .models import CommitteeInfo, Committee


class CommitteeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommitteeInfo
        fields = (
            "id",
            "committeeid",
            "committeename",
            "street1",
            "street2",
            "city",
            "state",
            "zipcode",
            "treasurerprefix",
            "treasurerfirstname",
            "text",
            "reason",
            "treasurermiddlename",
            "treasurerlastname",
            "treasurersuffix",
            "filename",
            "file",
            "created_at",
            "is_submitted",
            "signee",
            "email_on_file",
            "email_on_file_1",
            "additional_email_1",
            "additional_email_2",
            "form_type",
            "coverage_start_date",
            "coverage_end_date",
            "updated_at",
        )
        # read_only_fields = ('created_at', 'updated_at')

        # Methods to save the model objects to the database

    def create(self, validated_data):
        return CommitteeInfo.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.id = validated_data.get("id", instance.id)
        instance.committeeid = validated_data.get("committeeid", instance.committeeid)
        instance.committeename = validated_data.get(
            "committeename", instance.committeename
        )
        instance.street1 = validated_data.get("street1", instance.street1)
        instance.street2 = validated_data.get("street2", instance.street2)
        instance.city = validated_data.get("city", instance.city)
        instance.state = validated_data.get("state", instance.state)
        instance.text = validated_data.get("text", instance.text)
        instance.reason = validated_data.get("reason", instance.reason)
        instance.zipcode = validated_data.get("zipcode", instance.zipcode)
        instance.treasurerlastname = validated_data.get(
            "treasurerlastname", instance.treasurerlastname
        )
        instance.treasurerfirstname = validated_data.get(
            "treasurerfirstname", instance.treasurerfirstname
        )
        instance.treasurermiddlename = validated_data.get(
            "treasurermiddlename", instance.treasurermiddlename
        )
        instance.treasurerprefix = validated_data.get(
            "treasurerprefix", instance.treasurerprefix
        )
        instance.treasurersuffix = validated_data.get(
            "treasurersuffix", instance.treasurersuffix
        )
        instance.is_submitted = validated_data.get(
            "is_submitted", instance.is_submitted
        )
        instance.signee = validated_data.get("signee", instance.signee)
        instance.email_on_file = validated_data.get(
            "email_on_file", instance.email_on_file
        )
        instance.email_on_file_1 = validated_data.get(
            "email_on_file_1", instance.email_on_file_1
        )
        instance.additional_email_1 = validated_data.get(
            "additional_email_1", instance.additional_email_1
        )
        instance.additional_email_2 = validated_data.get(
            "additional_email_2", instance.additional_email_2
        )
        instance.form_type = validated_data.get("form_type", instance.form_type)
        instance.coverage_start_date = validated_data.get(
            "coverage_start_date", instance.coverage_start_date
        )
        instance.coverage_end_date = validated_data.get(
            "coverage_end_date", instance.coverage_end_date
        )
        instance.updated_at = validated_data.get("updated_at", instance.updated_at)
        instance.created_at = validated_data.get("created_at", instance.created_at)
        try:
            instance.filename = validated_data.get("filename", instance.filename)
            instance.file = validated_data.get("file", instance.file)
        except BaseException:
            pass

        instance.save()
        return instance


class CommitteeInfoListSerializer(serializers.ListSerializer):
    child = CommitteeInfoSerializer()
    allow_null = True
    many = True


class CommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Committee
        fields = (
            "committeeid",
            "committeename",
            "street1",
            "street2",
            "city",
            "state",
            "zipcode",
            "treasurerprefix",
            "treasurerfirstname",
            "treasurermiddlename",
            "treasurerlastname",
            "treasurersuffix",
            "email_on_file",
            "email_on_file_1",
            "created_at",
        )
        read_only_fields = ("created_at", "updated_at")

    # Methods to save the model objects to the database

    def create(self, validated_data):
        return Committee.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.committeeid = validated_data.get("committeeid", instance.committeeid)
        instance.committeename = validated_data.get(
            "committeename", instance.committeename
        )
        instance.street1 = validated_data.get("street1", instance.street1)
        instance.street2 = validated_data.get("street2", instance.street2)
        instance.city = validated_data.get("city", instance.city)
        instance.state = validated_data.get("state", instance.state)
        instance.zipcode = validated_data.get("zipcode", instance.zipcode)
        instance.treasurerlastname = validated_data.get(
            "treasurerlastname", instance.treasurerlastname
        )
        instance.treasurerfirstname = validated_data.get(
            "treasurerfirstname", instance.treasurerfirstname
        )
        instance.treasurermiddlename = validated_data.get(
            "treasurermiddlename", instance.treasurermiddletname
        )
        instance.treasurerprefix = validated_data.get(
            "treasurerprefix", instance.treasurerprefix
        )
        instance.treasurersuffix = validated_data.get(
            "treasurersuffix", instance.treasurersuffix
        )
        instance.email_on_file = validated_data.get(
            "email_on_file", instance.email_on_file
        )
        instance.email_on_file_1 = validated_data.get(
            "email_on_file_1", instance.email_on_file_1
        )
        instance.save()
        return instance
