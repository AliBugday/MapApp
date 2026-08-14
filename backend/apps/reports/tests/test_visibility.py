import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.reports.models import Report

from .conftest import PASSWORD
from .factories import ISTANBUL


def _create(client, **overrides):
    payload = {"title": "Test", **ISTANBUL, **overrides}
    return client.post("/api/reports/", payload, format="json")


@pytest.mark.django_db
def test_public_org_report_is_visible_to_everyone(
    client, auth_client, other_org_client, org_client
):
    created = _create(org_client, type="announcement", visibility="public")
    report_id = created.data["id"]

    for viewer in (client, auth_client, other_org_client):
        response = viewer.get("/api/reports/")
        assert report_id in [r["id"] for r in response.data["results"]]


@pytest.mark.django_db
def test_members_only_report_is_visible_only_to_the_posting_organization(
    client, auth_client, other_org_client, org_client
):
    created = _create(org_client, type="announcement", visibility="members")
    report_id = created.data["id"]

    for viewer in (client, auth_client, other_org_client):
        response = viewer.get("/api/reports/")
        assert report_id not in [r["id"] for r in response.data["results"]]

    response = org_client.get("/api/reports/")
    assert report_id in [r["id"] for r in response.data["results"]]


@pytest.mark.django_db
def test_members_only_report_retrieve_is_404_for_a_non_member(client, org_client):
    created = _create(org_client, type="event", visibility="members")
    report_id = created.data["id"]

    response = client.get(f"/api/reports/{report_id}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_members_only_report_retrieve_is_200_for_a_member(org_client):
    created = _create(org_client, type="event", visibility="members")
    report_id = created.data["id"]

    response = org_client.get(f"/api/reports/{report_id}/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_members_only_report_cannot_be_upvoted_by_a_non_member(auth_client, org_client):
    """Proves the filter in get_queryset() covers every route, not just list()."""
    created = _create(org_client, type="event", visibility="members")
    report_id = created.data["id"]

    response = auth_client.post(f"/api/reports/{report_id}/upvote/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_members_only_report_cannot_be_commented_on_by_a_non_member(auth_client, org_client):
    created = _create(org_client, type="event", visibility="members")
    report_id = created.data["id"]

    response = auth_client.post(f"/api/reports/{report_id}/comments/", {"body": "hi"})

    assert response.status_code == 404


@pytest.mark.django_db
def test_staff_can_see_members_only_reports_from_any_organization(org_client):
    created = _create(org_client, type="event", visibility="members")
    report_id = created.data["id"]

    staff = User.objects.create_user(username="staff", password=PASSWORD, is_staff=True)
    staff_client = APIClient()
    staff_client.force_authenticate(user=staff)

    response = staff_client.get(f"/api/reports/{report_id}/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_civic_reports_are_always_public_regardless_of_organization(client, org_client):
    """visibility=members is rejected for issue/request (test_types.py), so a civic report
    from an org member is still just an ordinary public report."""
    created = _create(org_client, type="issue")
    report_id = created.data["id"]

    response = client.get(f"/api/reports/{report_id}/")

    assert response.status_code == 200
    assert response.data["status"] == Report.Status.OPEN
