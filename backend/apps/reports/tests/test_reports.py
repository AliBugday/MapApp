import pytest
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.reports.models import Report

# Istanbul, roughly Sultanahmet.
ISTANBUL = {"latitude": 41.0082, "longitude": 28.9784}


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pw12345678")


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(client, user):
    client.force_authenticate(user=user)
    return client


def create_report(**kwargs):
    defaults = {
        "title": "Broken streetlight",
        "location": Point(ISTANBUL["longitude"], ISTANBUL["latitude"], srid=4326),
    }
    return Report.objects.create(**{**defaults, **kwargs})


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
def test_distance_query_is_in_metres():
    """The point of geography=True: radius filters use real metres, not degrees."""
    create_report()
    probe = Point(28.9784, 41.0217, srid=4326)  # ~1.5 km north

    assert Report.objects.filter(location__distance_lte=(probe, D(km=2))).count() == 1
    assert Report.objects.filter(location__distance_lte=(probe, D(m=500))).count() == 0
