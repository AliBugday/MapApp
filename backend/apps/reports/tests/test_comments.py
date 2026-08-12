import pytest

from apps.reports.models import Comment

from .factories import create_report


@pytest.mark.django_db
def test_posting_a_comment_attaches_it_to_the_report_and_author(auth_client, user):
    report = create_report()

    response = auth_client.post(
        f"/api/reports/{report.id}/comments/", {"body": "Still broken."}, format="json"
    )

    assert response.status_code == 201
    assert response.data["body"] == "Still broken."
    assert response.data["author_username"] == user.username
    comment = Comment.objects.get()
    assert comment.report == report
    assert comment.author == user


@pytest.mark.django_db
def test_comments_are_listed_oldest_first(auth_client):
    report = create_report()
    for body in ["first", "second", "third"]:
        auth_client.post(f"/api/reports/{report.id}/comments/", {"body": body}, format="json")

    response = auth_client.get(f"/api/reports/{report.id}/comments/")

    assert response.status_code == 200
    assert [c["body"] for c in response.data] == ["first", "second", "third"]


@pytest.mark.django_db
def test_anonymous_can_read_comments(client, auth_client):
    report = create_report()
    auth_client.post(f"/api/reports/{report.id}/comments/", {"body": "Visible"}, format="json")

    response = client.get(f"/api/reports/{report.id}/comments/")

    assert response.status_code == 200
    assert [c["body"] for c in response.data] == ["Visible"]


@pytest.mark.django_db
def test_anonymous_cannot_comment(client):
    report = create_report()

    response = client.post(f"/api/reports/{report.id}/comments/", {"body": "Sneaky"}, format="json")

    assert response.status_code in (401, 403)
    assert not Comment.objects.exists()


@pytest.mark.django_db
def test_an_empty_comment_is_rejected(auth_client):
    report = create_report()

    response = auth_client.post(f"/api/reports/{report.id}/comments/", {"body": ""}, format="json")

    assert response.status_code == 400
    assert "body" in response.data
    assert not Comment.objects.exists()


@pytest.mark.django_db
def test_comments_are_scoped_to_their_own_report(auth_client):
    """Guards against the action ignoring the pk and returning every comment."""
    first = create_report(title="First")
    second = create_report(title="Second")
    auth_client.post(f"/api/reports/{first.id}/comments/", {"body": "on first"}, format="json")
    auth_client.post(f"/api/reports/{second.id}/comments/", {"body": "on second"}, format="json")

    response = auth_client.get(f"/api/reports/{first.id}/comments/")

    assert [c["body"] for c in response.data] == ["on first"]


@pytest.mark.django_db
def test_the_payload_cannot_forge_the_author(auth_client, other_user, user):
    """author is read-only, so passing one is silently ignored rather than honoured."""
    report = create_report()

    response = auth_client.post(
        f"/api/reports/{report.id}/comments/",
        {"body": "Whose comment is this?", "author": other_user.id},
        format="json",
    )

    assert response.status_code == 201
    assert Comment.objects.get().author == user


@pytest.mark.django_db
def test_commenting_on_a_missing_report_is_404(auth_client):
    response = auth_client.post("/api/reports/999999/comments/", {"body": "Nowhere"}, format="json")

    assert response.status_code == 404
