from django.contrib.gis.geos import Polygon
from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Report, ReportImage, Upvote
from .serializers import (
    CommentSerializer,
    ReportImageSerializer,
    ReportSerializer,
    ReportStatusUpdateSerializer,
)


class IsAuthorOrStaffOrReadOnly(BasePermission):
    """Only the report's author (or staff) may PATCH it or attach an image.

    Object-level only: has_permission stays the default True, since every action this is
    used with already calls get_object() -> check_object_permissions(), and "who is the
    author" is only knowable once the object is in hand.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user.is_authenticated:
            return False
        return user.is_staff or obj.author_id == user.id


def parse_bbox(raw: str) -> Polygon:
    """Parse "minLng,minLat,maxLng,maxLat" into a polygon."""
    parts = raw.split(",")
    if len(parts) != 4:
        raise ValidationError({"bbox": "Virgülle ayrılmış dört değer bekleniyordu."})
    try:
        min_lng, min_lat, max_lng, max_lat = (float(p) for p in parts)
    except ValueError:
        raise ValidationError({"bbox": "Dört değerin tümü sayı olmalıdır."}) from None
    if min_lng >= max_lng or min_lat >= max_lat:
        raise ValidationError({"bbox": "Minimum değerler maksimum değerlerden küçük olmalıdır."})
    return Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))


class ReportViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        # PATCH can only ever change status — see ReportStatusUpdateSerializer's docstring
        # for why that's a separate serializer rather than reusing ReportSerializer.
        if self.action in ("update", "partial_update"):
            return ReportStatusUpdateSerializer
        return ReportSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "images"):
            return [IsAuthorOrStaffOrReadOnly()]
        return super().get_permissions()

    def get_queryset(self):
        # Explicit order_by, not just Meta.ordering: annotate() adds a GROUP BY, which
        # makes Django report the queryset as unordered and gives DRF unstable pagination.
        #
        # distinct=True on BOTH counts is required, not optional: annotating two Count()s
        # over different reverse FKs (upvotes and comments) in one queryset joins both
        # tables at once, producing a cartesian product — a report with 3 upvotes and 4
        # comments would otherwise report 12 of each.
        queryset = (
            Report.objects.select_related("author__organization")
            .prefetch_related("images")
            .annotate(
                upvote_count=Count("upvotes", distinct=True),
                comment_count=Count("comments", distinct=True),
            )
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

        # A members-only report is visible to anonymous/other users nowhere at all — not
        # in the list, and not via retrieve/upvote/comments either, since all three
        # resolve through get_object() -> this same queryset. That makes a non-member's
        # request 404, never 403: a 403 would confirm a hidden report exists at that id.
        if not user.is_staff:
            visible = Q(visibility=Report.Visibility.PUBLIC)
            if user.is_authenticated and user.organization_id:
                visible |= Q(
                    visibility=Report.Visibility.MEMBERS,
                    author__organization_id=user.organization_id,
                )
            queryset = queryset.filter(visible)

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

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        """List or add comments on one report.

        Returned as a flat array rather than a paginated envelope: a report's comments are
        read all at once on the detail page, and a second response shape would be one more
        thing for the frontend to special-case.

        The author comes from the session and the report from the URL, so neither can be
        forged through the payload. GET is public via IsAuthenticatedOrReadOnly; POST is not.
        """
        report = self.get_object()

        if request.method == "POST":
            serializer = CommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(report=report, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # select_related because the serializer reads author.username on every row.
        queryset = report.comments.select_related("author")
        return Response(CommentSerializer(queryset, many=True).data)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser])
    def images(self, request, pk=None):
        """Attach a photo to a report.

        A separate request from create_report() rather than accepting a file on the
        report's own JSON payload — mixing JSON and multipart in one request complicates
        both. Restricted to the author (or staff) via IsAuthorOrStaffOrReadOnly, applied in
        get_permissions() above.
        """
        report = self.get_object()
        image_file = request.FILES.get("image")
        if not image_file:
            raise ValidationError({"image": "Bir görsel dosyası gerekli."})
        report_image = ReportImage.objects.create(report=report, image=image_file)
        return Response(
            ReportImageSerializer(report_image).data,
            status=status.HTTP_201_CREATED,
        )
