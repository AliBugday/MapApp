import pytest
from django.utils import timezone

from apps.reports.models import EventRSVP, Report

from .factories import ISTANBUL, create_report

FUTURE_START = timezone.now() + timezone.timedelta(days=1)
FUTURE_END = FUTURE_START + timezone.timedelta(hours=2)
PAST_START = timezone.now() - timezone.timedelta(days=2)
PAST_END = PAST_START + timezone.timedelta(hours=2)


@pytest.mark.django_db
def test_event_requires_start_and_end_time(org_client):
    response = org_client.post(
        "/api/reports/", {"title": "Mahalle şenliği", "type": "event", **ISTANBUL}, format="json"
    )

    assert response.status_code == 400
    assert "event_starts_at" in response.data


@pytest.mark.django_db
def test_event_end_must_be_after_start(org_client):
    response = org_client.post(
        "/api/reports/",
        {
            "title": "Mahalle şenliği",
            "type": "event",
            "event_starts_at": FUTURE_END.isoformat(),
            "event_ends_at": FUTURE_START.isoformat(),
            **ISTANBUL,
        },
        format="json",
    )

    assert response.status_code == 400
    assert "event_ends_at" in response.data


@pytest.mark.django_db
def test_event_with_valid_range_round_trips(org_client):
    response = org_client.post(
        "/api/reports/",
        {
            "title": "Mahalle şenliği",
            "type": "event",
            "event_starts_at": FUTURE_START.isoformat(),
            "event_ends_at": FUTURE_END.isoformat(),
            **ISTANBUL,
        },
        format="json",
    )

    assert response.status_code == 201
    report = Report.objects.get(id=response.data["id"])
    assert report.event_starts_at == FUTURE_START
    assert report.event_ends_at == FUTURE_END


@pytest.mark.django_db
def test_non_event_cannot_have_event_times(auth_client):
    response = auth_client.post(
        "/api/reports/",
        {
            "title": "Kırık kaldırım",
            "type": "issue",
            "event_starts_at": FUTURE_START.isoformat(),
            "event_ends_at": FUTURE_END.isoformat(),
            **ISTANBUL,
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_rsvp_is_idempotent(auth_client, user, org_user):
    report = create_report(
        author=org_user,
        type=Report.Type.EVENT,
        event_starts_at=FUTURE_START,
        event_ends_at=FUTURE_END,
    )

    auth_client.post(f"/api/reports/{report.id}/rsvp/")
    response = auth_client.post(f"/api/reports/{report.id}/rsvp/")

    assert response.status_code == 200
    assert response.data["rsvp_count"] == 1
    assert EventRSVP.objects.filter(report=report, user=user).count() == 1


@pytest.mark.django_db
def test_rsvp_delete_removes_it(auth_client, user, org_user):
    report = create_report(
        author=org_user,
        type=Report.Type.EVENT,
        event_starts_at=FUTURE_START,
        event_ends_at=FUTURE_END,
    )
    auth_client.post(f"/api/reports/{report.id}/rsvp/")

    response = auth_client.delete(f"/api/reports/{report.id}/rsvp/")

    assert response.status_code == 200
    assert response.data["rsvp_count"] == 0
    assert response.data["has_rsvped"] is False
    assert not EventRSVP.objects.filter(report=report, user=user).exists()


@pytest.mark.django_db
def test_anonymous_cannot_rsvp(client, org_user):
    report = create_report(
        author=org_user,
        type=Report.Type.EVENT,
        event_starts_at=FUTURE_START,
        event_ends_at=FUTURE_END,
    )

    response = client.post(f"/api/reports/{report.id}/rsvp/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_rsvp_on_non_event_type_is_400(auth_client, other_user):
    report = create_report(author=other_user, type=Report.Type.ISSUE)

    response = auth_client.post(f"/api/reports/{report.id}/rsvp/")

    assert response.status_code == 400


@pytest.mark.django_db
def test_rsvp_on_past_event_is_400(auth_client, org_user):
    report = create_report(
        author=org_user,
        type=Report.Type.EVENT,
        event_starts_at=PAST_START,
        event_ends_at=PAST_END,
    )

    response = auth_client.post(f"/api/reports/{report.id}/rsvp/")

    assert response.status_code == 400


@pytest.mark.django_db
def test_rsvp_on_members_only_event_by_non_member_is_404(auth_client, org_user):
    report = create_report(
        author=org_user,
        type=Report.Type.EVENT,
        visibility=Report.Visibility.MEMBERS,
        event_starts_at=FUTURE_START,
        event_ends_at=FUTURE_END,
    )

    response = auth_client.post(f"/api/reports/{report.id}/rsvp/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_upvote_on_event_type_is_400(auth_client, org_user):
    """RSVP and upvote would mean the same thing ("I care about this") for an event."""
    report = create_report(
        author=org_user,
        type=Report.Type.EVENT,
        event_starts_at=FUTURE_START,
        event_ends_at=FUTURE_END,
    )

    response = auth_client.post(f"/api/reports/{report.id}/upvote/")

    assert response.status_code == 400
