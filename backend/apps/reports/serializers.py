from django.contrib.gis.geos import Point
from rest_framework import serializers

from .models import Comment, Report, ReportImage


class CommentSerializer(serializers.ModelSerializer):
    """report and author are set from the URL and the session, never from the payload."""

    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "body", "author_username", "created_at"]
        read_only_fields = ["id", "author_username", "created_at"]


class ReportImageSerializer(serializers.ModelSerializer):
    """Read-only: images are attached through the dedicated upload action, never as a
    field on ReportSerializer, since that would mean mixing JSON and multipart payloads.

    Note: `/media/...` is served as plain static files (see config/urls.py), so these URLs
    are not access-controlled — unlike the report itself, a members-only report's image is
    reachable by anyone who has the URL. Acceptable for a demo; real access control would
    mean signed URLs, which is a S3 concern this project deliberately isn't taking on yet.
    """

    # Plain SerializerMethodFields rather than ImageField(source=...): DRF's ImageField
    # builds an *absolute* URL from the request when a "request" is in context (which the
    # nested use here inherits from ReportSerializer), and that request's host inside
    # Docker is "backend:8000" — unreachable from the browser. A relative "/media/..." path
    # is what the Next.js proxy (next.config.ts) actually forwards.
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = ReportImage
        fields = ["id", "url", "thumbnail_url"]

    def get_url(self, obj) -> str:
        return obj.image.url

    def get_thumbnail_url(self, obj) -> str:
        return obj.thumbnail.url


class ReportSerializer(serializers.ModelSerializer):
    """Exposes the PointField as plain latitude/longitude numbers.

    GeoJSON would be more standard, but flat lat/lng keeps the frontend simple and
    maps directly onto what Leaflet expects.
    """

    # A report is only ever hidden from the public because an organization chose to hide
    # it, and only announcement/event support that — see validate() below.
    ORG_ONLY_TYPES = {Report.Type.ANNOUNCEMENT, Report.Type.EVENT}

    latitude = serializers.FloatField(min_value=-90, max_value=90, write_only=True)
    longitude = serializers.FloatField(min_value=-180, max_value=180, write_only=True)
    author_username = serializers.CharField(source="author.username", read_only=True)
    organization_name = serializers.CharField(
        source="author.organization.name", read_only=True, allow_null=True
    )
    upvote_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    has_upvoted = serializers.SerializerMethodField()
    rsvp_count = serializers.SerializerMethodField()
    has_rsvped = serializers.SerializerMethodField()
    images = ReportImageSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "title",
            "description",
            "status",
            "type",
            "visibility",
            "event_starts_at",
            "event_ends_at",
            "latitude",
            "longitude",
            "author_username",
            "organization_name",
            "upvote_count",
            "comment_count",
            "has_upvoted",
            "rsvp_count",
            "has_rsvped",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def get_upvote_count(self, obj) -> int:
        # Annotated by the viewset on list/retrieve; absent on a just-created instance.
        return getattr(obj, "upvote_count", 0)

    def get_comment_count(self, obj) -> int:
        return getattr(obj, "comment_count", 0)

    def get_has_upvoted(self, obj) -> bool:
        # Same as above: a brand-new report has no annotation, and nobody has upvoted it.
        return bool(getattr(obj, "has_upvoted", False))

    def get_rsvp_count(self, obj) -> int:
        return getattr(obj, "rsvp_count", 0)

    def get_has_rsvped(self, obj) -> bool:
        return bool(getattr(obj, "has_rsvped", False))

    def validate(self, attrs):
        user = self.context["request"].user
        report_type = attrs.get("type", Report.Type.ISSUE)
        visibility = attrs.get("visibility", Report.Visibility.PUBLIC)

        if report_type in self.ORG_ONLY_TYPES and not getattr(user, "organization_id", None):
            raise serializers.ValidationError(
                {"type": "Duyuru ve etkinlik yalnızca kurum hesapları tarafından oluşturulabilir."}
            )
        # "Members only" has no meaning without an organization to be a member of, and
        # hiding a civic complaint from the public defeats the point of reporting it.
        if visibility == Report.Visibility.MEMBERS and report_type not in self.ORG_ONLY_TYPES:
            raise serializers.ValidationError(
                {"visibility": "Yalnızca duyuru ve etkinlikler üyelere özel olabilir."}
            )

        starts_at = attrs.get("event_starts_at")
        ends_at = attrs.get("event_ends_at")
        if report_type == Report.Type.EVENT:
            if starts_at is None or ends_at is None:
                raise serializers.ValidationError(
                    {"event_starts_at": "Etkinlik için başlangıç ve bitiş zamanı gereklidir."}
                )
            if ends_at <= starts_at:
                raise serializers.ValidationError(
                    {"event_ends_at": "Bitiş zamanı başlangıçtan sonra olmalıdır."}
                )
        elif starts_at is not None or ends_at is not None:
            raise serializers.ValidationError(
                {"event_starts_at": "Yalnızca etkinlikler başlangıç/bitiş zamanı içerebilir."}
            )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["latitude"] = instance.location.y
        data["longitude"] = instance.location.x
        return data

    def create(self, validated_data):
        latitude = validated_data.pop("latitude")
        longitude = validated_data.pop("longitude")
        # PostGIS point order is (x, y) == (longitude, latitude).
        validated_data["location"] = Point(longitude, latitude, srid=4326)
        return super().create(validated_data)


class ReportStatusUpdateSerializer(serializers.ModelSerializer):
    """The only thing PATCH /api/reports/{id}/ can change.

    A separate serializer rather than reusing ReportSerializer for updates: that one marks
    `status` read-only (it must stay that way for create), and a single serializer that's
    read-only in one context and writable in another is a harder rule for the next reader
    to follow than two small serializers with one job each.
    """

    class Meta:
        model = Report
        fields = ["status"]
