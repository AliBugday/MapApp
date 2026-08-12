import pytest

from apps.reports.models import Upvote

from .factories import create_report


@pytest.mark.django_db
def test_upvote_adds_one(auth_client, user):
    report = create_report()

    response = auth_client.post(f"/api/reports/{report.id}/upvote/")

    assert response.status_code == 200
    assert response.data == {"upvote_count": 1, "has_upvoted": True}
    assert Upvote.objects.filter(report=report, user=user).count() == 1


@pytest.mark.django_db
def test_upvoting_twice_does_not_inflate_the_count(auth_client):
    """The behaviour the row-per-upvote model exists for: a double-tap is harmless."""
    report = create_report()

    auth_client.post(f"/api/reports/{report.id}/upvote/")
    response = auth_client.post(f"/api/reports/{report.id}/upvote/")

    assert response.status_code == 200
    assert response.data == {"upvote_count": 1, "has_upvoted": True}
    assert Upvote.objects.filter(report=report).count() == 1


@pytest.mark.django_db
def test_delete_removes_the_upvote(auth_client):
    report = create_report()
    auth_client.post(f"/api/reports/{report.id}/upvote/")

    response = auth_client.delete(f"/api/reports/{report.id}/upvote/")

    assert response.status_code == 200
    assert response.data == {"upvote_count": 0, "has_upvoted": False}
    assert not Upvote.objects.filter(report=report).exists()


@pytest.mark.django_db
def test_delete_without_an_existing_upvote_is_not_an_error(auth_client):
    """Idempotent in both directions, so the UI can't get stuck out of sync."""
    report = create_report()

    response = auth_client.delete(f"/api/reports/{report.id}/upvote/")

    assert response.status_code == 200
    assert response.data == {"upvote_count": 0, "has_upvoted": False}


@pytest.mark.django_db
def test_anonymous_cannot_upvote(client):
    report = create_report()

    response = client.post(f"/api/reports/{report.id}/upvote/")

    assert response.status_code in (401, 403)
    assert not Upvote.objects.exists()


@pytest.mark.django_db
def test_upvotes_from_two_users_both_count(auth_client, client, other_user):
    report = create_report()
    auth_client.post(f"/api/reports/{report.id}/upvote/")

    client.force_authenticate(user=other_user)
    response = client.post(f"/api/reports/{report.id}/upvote/")

    assert response.data == {"upvote_count": 2, "has_upvoted": True}


@pytest.mark.django_db
def test_one_users_upvote_does_not_show_as_anothers(auth_client, client, other_user):
    """has_upvoted must be per-request-user, not "does this report have any upvote"."""
    report = create_report()
    auth_client.post(f"/api/reports/{report.id}/upvote/")

    client.force_authenticate(user=other_user)
    response = client.get(f"/api/reports/{report.id}/")

    assert response.data["upvote_count"] == 1
    assert response.data["has_upvoted"] is False


@pytest.mark.django_db
def test_list_reports_reports_has_upvoted_for_the_current_user(auth_client):
    upvoted = create_report(title="Upvoted")
    create_report(title="Not upvoted")
    auth_client.post(f"/api/reports/{upvoted.id}/upvote/")

    results = {r["title"]: r for r in auth_client.get("/api/reports/").data["results"]}

    assert results["Upvoted"]["has_upvoted"] is True
    assert results["Not upvoted"]["has_upvoted"] is False


@pytest.mark.django_db
def test_has_upvoted_is_false_for_anonymous_readers(client):
    """Anonymous users get the field too, so the response shape never changes."""
    report = create_report()

    response = client.get(f"/api/reports/{report.id}/")

    assert response.data["has_upvoted"] is False


@pytest.mark.django_db
def test_upvote_on_a_missing_report_is_404(auth_client):
    response = auth_client.post("/api/reports/999999/upvote/")

    assert response.status_code == 404
