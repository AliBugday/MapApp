"""PATCH /api/auth/me/ — setting/clearing a user's home and work locations."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User

PASSWORD = "demo-pw-9f2b"

# Istanbul, roughly Sultanahmet / Kadıköy.
HOME = {"latitude": 41.0082, "longitude": 28.9784}
WORK = {"latitude": 40.9909, "longitude": 29.0304}


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def existing_user(db):
    return User.objects.create_user(username="tester", password=PASSWORD)


@pytest.fixture
def logged_in_client(client, existing_user):
    client.post("/api/auth/login/", {"username": "tester", "password": PASSWORD}, format="json")
    return client


@pytest.mark.django_db
def test_patch_me_sets_and_round_trips_home_and_work_location(logged_in_client):
    response = logged_in_client.patch("/api/auth/me/", {"home": HOME, "work": WORK}, format="json")

    assert response.status_code == 200
    user = response.data["user"]
    assert user["home_latitude"] == pytest.approx(HOME["latitude"])
    assert user["home_longitude"] == pytest.approx(HOME["longitude"])
    assert user["work_latitude"] == pytest.approx(WORK["latitude"])
    assert user["work_longitude"] == pytest.approx(WORK["longitude"])


@pytest.mark.django_db
def test_patch_me_can_clear_a_location_by_sending_null(logged_in_client):
    logged_in_client.patch("/api/auth/me/", {"home": HOME}, format="json")

    response = logged_in_client.patch("/api/auth/me/", {"home": None}, format="json")

    assert response.status_code == 200
    assert response.data["user"]["home_latitude"] is None
    assert response.data["user"]["home_longitude"] is None


@pytest.mark.django_db
def test_patch_me_partial_update_leaves_the_other_location_untouched(logged_in_client):
    logged_in_client.patch("/api/auth/me/", {"home": HOME, "work": WORK}, format="json")

    response = logged_in_client.patch("/api/auth/me/", {"home": None}, format="json")

    assert response.data["user"]["home_latitude"] is None
    assert response.data["user"]["work_latitude"] == pytest.approx(WORK["latitude"])


@pytest.mark.django_db
def test_anonymous_patch_me_is_403(client):
    response = client.patch("/api/auth/me/", {"home": HOME}, format="json")

    assert response.status_code == 403


@pytest.mark.django_db
def test_invalid_latitude_is_400(logged_in_client):
    response = logged_in_client.patch(
        "/api/auth/me/", {"home": {"latitude": 200, "longitude": 29}}, format="json"
    )

    assert response.status_code == 400
