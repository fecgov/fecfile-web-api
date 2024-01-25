from rest_framework import serializers
from fecfiler.user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "is_active",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
        )
