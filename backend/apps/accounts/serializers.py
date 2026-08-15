from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """The single shape a user is exposed as, shared by all four auth endpoints."""

    organization_name = serializers.CharField(
        source="organization.name", read_only=True, allow_null=True
    )
    organization_kind = serializers.CharField(
        source="organization.kind", read_only=True, allow_null=True
    )
    # Flattened from the PointFields rather than exposed as GeoJSON, same reasoning as
    # ReportSerializer's latitude/longitude — plain numbers are what the frontend map wants.
    home_latitude = serializers.SerializerMethodField()
    home_longitude = serializers.SerializerMethodField()
    work_latitude = serializers.SerializerMethodField()
    work_longitude = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "organization_name",
            "organization_kind",
            "home_latitude",
            "home_longitude",
            "work_latitude",
            "work_longitude",
        ]
        read_only_fields = fields

    def get_home_latitude(self, obj):
        return obj.home_location.y if obj.home_location else None

    def get_home_longitude(self, obj):
        return obj.home_location.x if obj.home_location else None

    def get_work_latitude(self, obj):
        return obj.work_location.y if obj.work_location else None

    def get_work_longitude(self, obj):
        return obj.work_location.x if obj.work_location else None


class LatLngSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class LocationUpdateSerializer(serializers.Serializer):
    """PATCH /api/auth/me/'s payload shape.

    A plain Serializer, not a ModelSerializer — it's not writing the whole user. A key's
    *absence* leaves that location untouched; its *presence* fully replaces it (a
    {latitude, longitude} object to set it, or null to clear it). That gives clean partial-
    update semantics without needing two separate endpoints.
    """

    home = LatLngSerializer(required=False, allow_null=True)
    work = LatLngSerializer(required=False, allow_null=True)


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
