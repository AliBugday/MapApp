from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """The single shape a user is exposed as, shared by all four auth endpoints."""

    organization_name = serializers.CharField(
        source="organization.name", read_only=True, allow_null=True
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "organization_name"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    # validate_password applies the AUTH_PASSWORD_VALIDATORS already in settings, so the
    # rules live in one place instead of being restated here.
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        # create_user rather than create: it hashes the password.
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
