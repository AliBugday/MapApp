"""notify_nearby_users(), exercised through POST /api/reports/ (perform_create) rather than
called directly — the thing under test is that the trigger actually fires from the real
write path, not just that the function is correct in isolation.
"""

import pytest
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.reports.tests.factories import ISTANBUL, create_organization

from .conftest import PASSWORD

FUTURE_START = timezone.now() + timezone.timedelta(days=1)
FUTURE_END = FUTURE_START + timezone.timedelta(hours=2)

# A few hundred metres from ISTANBUL — well inside the default 5 km radius.
NEARBY = {"latitude": 41.0090, "longitude": 28.9790}
# Ankara — nowhere near Istanbul.
FAR_AWAY = {"latitude": 39.9334, "longitude": 32.8597}


def _create_event(client, **overrides):
    payload = {
        "title": "Mahalle şenliği",
        "type": "event",
        "event_starts_at": FUTURE_START.isoformat(),
        "event_ends_at": FUTURE_END.isoformat(),
        **ISTANBUL,
        **overrides,
    }
    return client.post("/api/reports/", payload, format="json")


@pytest.mark.django_db
def test_notify_creates_notification_for_a_user_with_home_nearby(org_client):
    nearby_user = User.objects.create_user(
        username="nearby-home",
        password=PASSWORD,
        home_location=Point(NEARBY["longitude"], NEARBY["latitude"], srid=4326),
    )

    response = _create_event(org_client)

    assert response.status_code == 201
    assert Notification.objects.filter(
        recipient=nearby_user, report_id=response.data["id"]
    ).exists()


@pytest.mark.django_db
def test_notify_creates_notification_for_a_user_with_work_nearby(org_client):
    nearby_user = User.objects.create_user(
        username="nearby-work",
        password=PASSWORD,
        work_location=Point(NEARBY["longitude"], NEARBY["latitude"], srid=4326),
    )

    response = _create_event(org_client)

    assert Notification.objects.filter(
        recipient=nearby_user, report_id=response.data["id"]
    ).exists()


@pytest.mark.django_db
def test_notify_skips_users_outside_the_radius(org_client):
    far_user = User.objects.create_user(
        username="far-away",
        password=PASSWORD,
        home_location=Point(FAR_AWAY["longitude"], FAR_AWAY["latitude"], srid=4326),
    )

    _create_event(org_client)

    assert not Notification.objects.filter(recipient=far_user).exists()


@pytest.mark.django_db
def test_notify_skips_the_events_own_author(org_client, org_user):
    org_user.home_location = Point(ISTANBUL["longitude"], ISTANBUL["latitude"], srid=4326)
    org_user.save()

    _create_event(org_client)

    assert not Notification.objects.filter(recipient=org_user).exists()


@pytest.mark.django_db
def test_notify_triggers_for_a_plain_issue(auth_client):
    """Not event-only — any nearby report type notifies."""
    nearby_user = User.objects.create_user(
        username="nearby-issue",
        password=PASSWORD,
        home_location=Point(NEARBY["longitude"], NEARBY["latitude"], srid=4326),
    )

    response = auth_client.post(
        "/api/reports/", {"title": "Kırık kaldırım", "type": "issue", **ISTANBUL}, format="json"
    )

    assert Notification.objects.filter(
        recipient=nearby_user, report_id=response.data["id"]
    ).exists()


@pytest.mark.django_db
def test_notify_triggers_for_a_request(auth_client):
    nearby_user = User.objects.create_user(
        username="nearby-request",
        password=PASSWORD,
        home_location=Point(NEARBY["longitude"], NEARBY["latitude"], srid=4326),
    )

    response = auth_client.post(
        "/api/reports/",
        {"title": "Yeni park talebi", "type": "request", **ISTANBUL},
        format="json",
    )

    assert Notification.objects.filter(
        recipient=nearby_user, report_id=response.data["id"]
    ).exists()


@pytest.mark.django_db
def test_notify_triggers_for_a_public_announcement(org_client):
    nearby_user = User.objects.create_user(
        username="nearby-announcement",
        password=PASSWORD,
        home_location=Point(NEARBY["longitude"], NEARBY["latitude"], srid=4326),
    )

    response = org_client.post(
        "/api/reports/", {"title": "Duyuru", "type": "announcement", **ISTANBUL}, format="json"
    )

    assert Notification.objects.filter(
        recipient=nearby_user, report_id=response.data["id"]
    ).exists()


@pytest.mark.django_db
def test_notify_skips_non_members_for_a_members_only_event(org_client, org_user):
    same_org_member = User.objects.create_user(
        username="same-org-member",
        password=PASSWORD,
        organization=org_user.organization,
        home_location=Point(NEARBY["longitude"], NEARBY["latitude"], srid=4326),
    )
    non_member = User.objects.create_user(
        username="non-member",
        password=PASSWORD,
        home_location=Point(NEARBY["longitude"], NEARBY["latitude"], srid=4326),
    )
    other_org = create_organization(name="Başka Belediye")
    other_org_member = User.objects.create_user(
        username="other-org-member",
        password=PASSWORD,
        organization=other_org,
        home_location=Point(NEARBY["longitude"], NEARBY["latitude"], srid=4326),
    )

    response = _create_event(org_client, visibility="members")

    report_id = response.data["id"]
    assert Notification.objects.filter(recipient=same_org_member, report_id=report_id).exists()
    assert not Notification.objects.filter(recipient=non_member).exists()
    assert not Notification.objects.filter(recipient=other_org_member).exists()
