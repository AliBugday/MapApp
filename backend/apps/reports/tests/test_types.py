import pytest
from django.utils import timezone

from .factories import ISTANBUL


def _create(client, **overrides):
    payload = {"title": "Test", **ISTANBUL, **overrides}
    # Events now require a start/end time — fill in a plausible future range by default so
    # tests about type/visibility rules don't also have to know about event scheduling.
    if payload.get("type") == "event" and "event_starts_at" not in payload:
        starts_at = timezone.now() + timezone.timedelta(days=1)
        payload["event_starts_at"] = starts_at.isoformat()
        payload["event_ends_at"] = (starts_at + timezone.timedelta(hours=2)).isoformat()
    return client.post("/api/reports/", payload, format="json")


@pytest.mark.django_db
@pytest.mark.parametrize("report_type", ["announcement", "event"])
def test_org_only_type_rejected_without_an_organization(auth_client, report_type):
    response = _create(auth_client, type=report_type)

    assert response.status_code == 400
    assert "type" in response.data


@pytest.mark.django_db
@pytest.mark.parametrize("report_type", ["announcement", "event"])
def test_org_only_type_allowed_for_an_org_member(org_client, report_type):
    response = _create(org_client, type=report_type)

    assert response.status_code == 201
    assert response.data["type"] == report_type


@pytest.mark.django_db
@pytest.mark.parametrize("report_type", ["issue", "request"])
def test_civic_types_allowed_for_any_signed_in_user(auth_client, report_type):
    response = _create(auth_client, type=report_type)

    assert response.status_code == 201


@pytest.mark.django_db
def test_members_only_visibility_rejected_for_civic_types(org_client):
    response = _create(org_client, type="issue", visibility="members")

    assert response.status_code == 400
    assert "visibility" in response.data


@pytest.mark.django_db
def test_members_only_visibility_allowed_for_org_only_types(org_client):
    response = _create(org_client, type="event", visibility="members")

    assert response.status_code == 201
    assert response.data["visibility"] == "members"
