from django.contrib.gis.geos import Polygon
from django.db.models import BooleanField, Count, Exists, OuterRef, Value
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Report, Upvote
from .serializers import ReportSerializer


def parse_bbox(raw: str) -> Polygon:
    """Parse "minLng,minLat,maxLng,maxLat" into a polygon."""
    parts = raw.split(",")
    if len(parts) != 4:
        raise ValidationError({"bbox": "Expected four comma-separated values."})
    try:
        min_lng, min_lat, max_lng, max_lat = (float(p) for p in parts)
    except ValueError:
        raise ValidationError({"bbox": "All four values must be numbers."}) from None
    if min_lng >= max_lng or min_lat >= max_lat:
        raise ValidationError({"bbox": "Minimum values must be smaller than maximum values."})
    return Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))


class ReportViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Explicit order_by, not just Meta.ordering: annotate() adds a GROUP BY, which
        # makes Django report the queryset as unordered and gives DRF unstable pagination.
        queryset = (
            Report.objects.select_related("author")
            .annotate(upvote_count=Count("upvotes"))
            .order_by("-created_at")
        )

        # has_upvoted comes from the database as a subquery rather than a per-report
        # lookup in the serializer, which would be one extra query per marker.
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                has_upvoted=Exists(Upvote.objects.filter(report=OuterRef("pk"), user=user))
            )
        else:
            # Annotated as a constant so the field is always present in the response,
            # rather than the shape changing depending on who is asking.
            queryset = queryset.annotate(has_upvoted=Value(False, output_field=BooleanField()))

        bbox = self.request.query_params.get("bbox")
        if bbox:
            polygon = parse_bbox(bbox)
            polygon.srid = 4326
            # ST_Intersects rather than ST_Within: PostGIS geography columns don't
            # support ST_Within, and for points the two are equivalent.
            queryset = queryset.filter(location__intersects=polygon)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post", "delete"])
    def upvote(self, request, pk=None):
        """Add or remove the current user's upvote.

        POST is idempotent via get_or_create: a double-tap, or a retried request on a
        flaky connection, cannot inflate the count. The unique_upvote_per_user constraint
        backs this at the database level, and get_or_create turns the resulting
        IntegrityError from a concurrent race into a plain get.

        Both methods return the same shape so the frontend has one way to reconcile its
        optimistic update, and the count is re-queried rather than derived from the
        annotation, which was computed before this write.

        IsAuthenticatedOrReadOnly already covers this: POST and DELETE are both unsafe
        methods, so an anonymous caller gets a 403 without a separate permission class.
        """
        report = self.get_object()
        if request.method == "POST":
            Upvote.objects.get_or_create(report=report, user=request.user)
            has_upvoted = True
        else:
            Upvote.objects.filter(report=report, user=request.user).delete()
            has_upvoted = False
        return Response({"upvote_count": report.upvotes.count(), "has_upvoted": has_upvoted})
