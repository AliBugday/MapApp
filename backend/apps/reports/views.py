from django.contrib.gis.geos import Polygon
from django.db.models import Count
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Report
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
