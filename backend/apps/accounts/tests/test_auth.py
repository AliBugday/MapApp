"""Auth endpoint tests.

These deliberately use a plain APIClient and the real login/session flow rather than
force_authenticate, which bypasses session login entirely — the session round trip is
exactly what is under test here.
"""

import json

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User

PASSWORD = "demo-pw-9f2b"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def existing_user(db):
    return User.objects.create_user(username="tester", password=PASSWORD)


@pytest.mark.django_db
def test_register_creates_the_user_and_signs_them_in(client):
    response = client.post(
        "/api/auth/register/",
        {"username": "newcomer", "password": PASSWORD},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["username"] == "newcomer"
    assert "password" not in response.data
    assert User.objects.filter(username="newcomer").exists()

    # The session cookie from register carries over: no separate login needed.
    assert client.get("/api/auth/me/").data["user"]["username"] == "newcomer"


@pytest.mark.django_db
def test_register_hashes_the_password(client):
    client.post(
        "/api/auth/register/", {"username": "newcomer", "password": PASSWORD}, format="json"
    )

    user = User.objects.get(username="newcomer")
    assert user.password != PASSWORD
    assert user.check_password(PASSWORD)


@pytest.mark.django_db
def test_register_rejects_a_weak_password(client):
    """Proves AUTH_PASSWORD_VALIDATORS are actually wired in through validate_password."""
    response = client.post(
        "/api/auth/register/", {"username": "newcomer", "password": "123"}, format="json"
    )

    assert response.status_code == 400
    assert "password" in response.data
    assert not User.objects.filter(username="newcomer").exists()


@pytest.mark.django_db
def test_register_rejects_a_duplicate_username(client, existing_user):
    response = client.post(
        "/api/auth/register/", {"username": "tester", "password": PASSWORD}, format="json"
    )

    assert response.status_code == 400
    assert "username" in response.data
    assert User.objects.filter(username="tester").count() == 1


@pytest.mark.django_db
def test_login_with_correct_credentials_starts_a_session(client, existing_user):
    response = client.post(
        "/api/auth/login/", {"username": "tester", "password": PASSWORD}, format="json"
    )

    assert response.status_code == 200
    assert response.data["username"] == "tester"
    assert client.get("/api/auth/me/").data["user"]["username"] == "tester"


@pytest.mark.django_db
def test_login_with_a_wrong_password_is_rejected(client, existing_user):
    response = client.post(
        "/api/auth/login/", {"username": "tester", "password": "not-the-password"}, format="json"
    )

    assert response.status_code == 400
    assert client.get("/api/auth/me/").data["user"] is None


@pytest.mark.django_db
def test_login_for_an_unknown_user_gives_the_same_error(client):
    """Same message as a wrong password, so usernames can't be enumerated."""
    response = client.post(
        "/api/auth/login/", {"username": "ghost", "password": PASSWORD}, format="json"
    )

    assert response.status_code == 400
    assert response.data["detail"] == "Incorrect username or password."


@pytest.mark.django_db
def test_me_is_null_for_anonymous_visitors(client):
    response = client.get("/api/auth/me/")

    assert response.status_code == 200
    assert response.data["user"] is None
    # Asserted against the rendered body, not response.data: a bare Response(None) has a
    # populated .data but renders as zero bytes, which makes response.json() throw in the
    # browser. Only the rendered content catches that.
    assert json.loads(response.content) == {"user": None}


@pytest.mark.django_db
def test_me_sets_the_csrf_cookie(client):
    """Without this, a returning visitor's next POST fails CSRF validation."""
    response = client.get("/api/auth/me/")

    assert "csrftoken" in response.cookies


@pytest.mark.django_db
def test_logout_ends_the_session(client, existing_user):
    client.post("/api/auth/login/", {"username": "tester", "password": PASSWORD}, format="json")

    response = client.post("/api/auth/logout/")

    assert response.status_code == 204
    assert client.get("/api/auth/me/").data["user"] is None


@pytest.mark.django_db
def test_session_login_authorises_creating_a_report(client, existing_user):
    """The end the whole step exists for: signing in is enough to post a report."""
    client.post("/api/auth/login/", {"username": "tester", "password": PASSWORD}, format="json")

    response = client.post(
        "/api/reports/",
        {"title": "Broken streetlight", "latitude": 41.0082, "longitude": 28.9784},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["author_username"] == "tester"
