import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.reports.models import Report

from .conftest import PASSWORD
from .factories import create_report


@pytest.mark.django_db
def test_author_can_change_status(auth_client, user):
    report = create_report(author=user)

    response = auth_client.patch(
        f"/api/reports/{report.id}/", {"status": "resolved"}, format="json"
    )

    assert response.status_code == 200
    report.refresh_from_db()
    assert report.status == Report.Status.RESOLVED


@pytest.mark.django_db
def test_non_author_cannot_change_status(auth_client, other_user):
    report = create_report(author=other_user, status=Report.Status.OPEN)

    response = auth_client.patch(
        f"/api/reports/{report.id}/", {"status": "resolved"}, format="json"
    )

    assert response.status_code == 403
    report.refresh_from_db()
    assert report.status == Report.Status.OPEN


@pytest.mark.django_db
def test_anonymous_cannot_change_status(client, user):
    report = create_report(author=user, status=Report.Status.OPEN)

    response = client.patch(f"/api/reports/{report.id}/", {"status": "resolved"}, format="json")

    assert response.status_code == 403


@pytest.mark.django_db
def test_staff_can_change_any_report_status(other_user):
    report = create_report(author=other_user, status=Report.Status.OPEN)
    staff = User.objects.create_user(username="staff", password=PASSWORD, is_staff=True)
    staff_client = APIClient()
    staff_client.force_authenticate(user=staff)

    response = staff_client.patch(
        f"/api/reports/{report.id}/", {"status": "resolved"}, format="json"
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_patch_cannot_change_title_or_type(auth_client, user):
    """Only status is writable via PATCH — see ReportStatusUpdateSerializer."""
    report = create_report(author=user, title="Original title", type=Report.Type.ISSUE)

    response = auth_client.patch(
        f"/api/reports/{report.id}/",
        {"status": "resolved", "title": "Hijacked title", "type": "event"},
        format="json",
    )

    assert response.status_code == 200
    report.refresh_from_db()
    assert report.title == "Original title"
    assert report.type == Report.Type.ISSUE
