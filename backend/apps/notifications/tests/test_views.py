import pytest

from apps.notifications.models import Notification
from apps.reports.tests.factories import create_report


@pytest.mark.django_db
def test_list_returns_only_the_requesting_users_own_notifications(auth_client, user, other_user):
    report = create_report(author=other_user)
    Notification.objects.create(recipient=user, report=report)
    Notification.objects.create(recipient=other_user, report=report)

    response = auth_client.get("/api/notifications/")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["report_id"] == report.id


@pytest.mark.django_db
def test_mark_all_read_only_affects_that_users_unread_ones(auth_client, user, other_user):
    report = create_report(author=other_user)
    mine = Notification.objects.create(recipient=user, report=report)
    theirs = Notification.objects.create(recipient=other_user, report=report)

    response = auth_client.post("/api/notifications/")

    assert response.status_code == 204
    mine.refresh_from_db()
    theirs.refresh_from_db()
    assert mine.is_read is True
    assert theirs.is_read is False


@pytest.mark.django_db
def test_anonymous_cannot_list_or_mark_read(client):
    assert client.get("/api/notifications/").status_code == 403
    assert client.post("/api/notifications/").status_code == 403
