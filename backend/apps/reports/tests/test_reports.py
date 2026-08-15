import pytest
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from apps.reports.models import Comment, EventRSVP, Report, Upvote

from .factories import ISTANBUL, create_report


@pytest.mark.django_db
def test_create_stores_the_point_in_lng_lat_order(auth_client, user):
    """Guards against the classic PostGIS mistake of swapping x/y."""
    response = auth_client.post("/api/reports/", {"title": "Pothole", **ISTANBUL}, format="json")

    assert response.status_code == 201
    report = Report.objects.get()
    assert report.location.x == pytest.approx(ISTANBUL["longitude"])
    assert report.location.y == pytest.approx(ISTANBUL["latitude"])
    assert report.author == user
    assert report.status == Report.Status.OPEN
    assert report.type == Report.Type.ISSUE
    assert report.visibility == Report.Visibility.PUBLIC


@pytest.mark.django_db
def test_create_round_trips_coordinates(auth_client):
    response = auth_client.post("/api/reports/", {"title": "Pothole", **ISTANBUL}, format="json")

    assert response.data["latitude"] == pytest.approx(ISTANBUL["latitude"])
    assert response.data["longitude"] == pytest.approx(ISTANBUL["longitude"])
    # Present on create as well as list, so the frontend sees one shape.
    assert response.data["upvote_count"] == 0


@pytest.mark.django_db
def test_anonymous_cannot_create(client):
    response = client.post("/api/reports/", {"title": "Pothole", **ISTANBUL}, format="json")

    assert response.status_code in (401, 403)
    assert Report.objects.count() == 0


@pytest.mark.django_db
def test_anonymous_can_read(client):
    create_report()

    response = client.get("/api/reports/")

    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_bbox_includes_report_inside_it(client):
    create_report()

    response = client.get("/api/reports/", {"bbox": "28.9,40.9,29.1,41.1"})

    assert response.data["count"] == 1


@pytest.mark.django_db
def test_bbox_excludes_report_outside_it(client):
    create_report()

    # Berlin.
    response = client.get("/api/reports/", {"bbox": "13.0,52.0,13.8,52.8"})

    assert response.data["count"] == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "bbox",
    [
        "1,2,3",  # too few values
        "a,b,c,d",  # not numbers
        "29.1,40.9,28.9,41.1",  # min longitude greater than max
    ],
)
def test_malformed_bbox_is_rejected(client, bbox):
    response = client.get("/api/reports/", {"bbox": bbox})

    assert response.status_code == 400


@pytest.mark.django_db
def test_upvote_comment_and_rsvp_counts_do_not_multiply_each_other(client, user, other_user):
    """Regression test for annotating three Count()s over different reverse FKs at once.

    Without distinct=True on all three, the join through upvotes, comments and rsvps
    produces a cartesian product: 2 upvotes x 3 comments x 1 rsvp would report inflated,
    mutually-multiplied totals rather than 2, 3 and 1.
    """
    report = create_report()
    Upvote.objects.create(report=report, user=user)
    Upvote.objects.create(report=report, user=other_user)
    for i in range(3):
        Comment.objects.create(report=report, author=user, body=f"Comment {i}")
    EventRSVP.objects.create(report=report, user=user)

    response = client.get(f"/api/reports/{report.id}/")

    assert response.data["upvote_count"] == 2
    assert response.data["comment_count"] == 3
    assert response.data["rsvp_count"] == 1


@pytest.mark.django_db
def test_distance_query_is_in_metres():
    """The point of geography=True: radius filters use real metres, not degrees."""
    create_report()
    probe = Point(28.9784, 41.0217, srid=4326)  # ~1.5 km north

    assert Report.objects.filter(location__distance_lte=(probe, D(km=2))).count() == 1
    assert Report.objects.filter(location__distance_lte=(probe, D(m=500))).count() == 0
