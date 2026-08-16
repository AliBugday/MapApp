"""notify_if_report_is_popular(), exercised through POST /api/reports/{id}/upvote/
(the ReportViewSet.upvote action) rather than called directly — the thing under test is
that the trigger actually fires from the real write path, not just that the function is
correct in isolation. Mirrors test_notify_nearby_users.py's approach.

POPULARITY_UPVOTE_THRESHOLD defaults to 3 and is inclusive, so 3 distinct upvoters is
the first count that reaches it — one user can only upvote a report once, so "3
upvotes" means 3 users.
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.reports.tests.factories import create_report

from .conftest import PASSWORD


def _upvote_as(report, username):
    upvoter = User.objects.create_user(username=username, password=PASSWORD)
    client = APIClient()
    client.force_authenticate(user=upvoter)
    return client.post(f"/api/reports/{report.id}/upvote/")


@pytest.mark.django_db
def test_notifies_author_once_upvotes_reach_the_threshold(user):
    report = create_report(author=user)

    for i in range(3):
        _upvote_as(report, f"upvoter-{i}")

    assert Notification.objects.filter(
        recipient=user, report=report, kind=Notification.Kind.POPULAR
    ).exists()


@pytest.mark.django_db
def test_does_not_notify_below_the_threshold(user):
    report = create_report(author=user)

    for i in range(2):
        _upvote_as(report, f"upvoter-{i}")

    assert not Notification.objects.filter(recipient=user, kind=Notification.Kind.POPULAR).exists()


@pytest.mark.django_db
def test_does_not_notify_again_on_further_upvotes(user):
    """popular_notified is a one-shot latch, not a re-triggering threshold check."""
    report = create_report(author=user)

    for i in range(6):
        _upvote_as(report, f"upvoter-{i}")

    assert (
        Notification.objects.filter(
            recipient=user, report=report, kind=Notification.Kind.POPULAR
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_recipient_is_the_author_not_the_upvoters(other_user):
    report = create_report(author=other_user)

    for i in range(3):
        _upvote_as(report, f"upvoter-{i}")

    popular = Notification.objects.filter(report=report, kind=Notification.Kind.POPULAR)
    assert popular.count() == 1
    assert popular.first().recipient_id == other_user.id


@pytest.mark.django_db
def test_report_with_no_author_does_not_error_or_notify():
    report = create_report(author=None)

    response = None
    for i in range(3):
        response = _upvote_as(report, f"upvoter-{i}")

    assert response.status_code == 200
    assert not Notification.objects.filter(report=report, kind=Notification.Kind.POPULAR).exists()


@pytest.mark.django_db
def test_nearby_notifications_are_unaffected(user):
    """The two kinds are independent — crossing the popularity threshold must not touch
    any already-created nearby notification, and vice versa isn't touched by this action
    at all since upvote never calls notify_nearby_users."""
    report = create_report(author=user)
    Notification.objects.create(recipient=user, report=report, kind=Notification.Kind.NEARBY)

    for i in range(3):
        _upvote_as(report, f"upvoter-{i}")

    assert Notification.objects.filter(recipient=user, kind=Notification.Kind.NEARBY).count() == 1
    assert Notification.objects.filter(recipient=user, kind=Notification.Kind.POPULAR).count() == 1
