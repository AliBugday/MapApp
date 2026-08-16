"""Explicit notification triggers — called directly from the write that causes them,
not via signals. A signal handler two files away from the write it reacts to is exactly
the kind of magic CLAUDE.md's "code another developer can follow" rules against.
"""

from django.conf import settings
from django.contrib.gis.measure import D
from django.db.models import Q

from apps.accounts.models import User
from apps.reports.models import Report

from .models import Notification


def notify_nearby_users(report: Report) -> None:
    """Notify every user whose home or work location is near a newly created report,
    of any type. Computing the radius here rather than at import time lets tests
    override NEARBY_NOTIFICATION_RADIUS_KM per-test.
    """
    radius = D(km=settings.NEARBY_NOTIFICATION_RADIUS_KM)
    nearby = Q(home_location__distance_lte=(report.location, radius)) | Q(
        work_location__distance_lte=(report.location, radius)
    )
    candidates = User.objects.filter(nearby).exclude(id=report.author_id)

    # Members-only reports (announcement/event) must not notify (and link to) one the
    # recipient can't open — same visibility rule already enforced in
    # ReportViewSet.get_queryset(). issue/request are always public, so this never
    # filters them.
    if report.visibility == Report.Visibility.MEMBERS:
        candidates = candidates.filter(organization_id=report.author.organization_id)

    # Q(...) | Q(...) naturally dedupes: a user whose home *and* work both fall in
    # range still matches the filter once, since it's on User, not on the matched field.
    Notification.objects.bulk_create(
        Notification(recipient=user, report=report, kind=Notification.Kind.NEARBY)
        for user in candidates
    )


def notify_if_report_is_popular(report: Report) -> None:
    """Tell a report's author the first time its upvote count reaches the threshold.

    The threshold is inclusive — reaching it triggers the notification, not just
    exceeding it. report.popular_notified is the idempotency guard: without it, every
    upvote past the threshold (the 4th, 5th, ...) would notify the author again.
    Reading the threshold from settings rather than at import time mirrors
    notify_nearby_users, so tests can override POPULARITY_UPVOTE_THRESHOLD per-test.
    """
    if report.popular_notified or report.author_id is None:
        return
    if report.upvotes.count() < settings.POPULARITY_UPVOTE_THRESHOLD:
        return
    Notification.objects.create(
        recipient=report.author, report=report, kind=Notification.Kind.POPULAR
    )
    report.popular_notified = True
    report.save(update_fields=["popular_notified"])
