"""One-time catch-up: notify_if_report_is_popular() only ever runs from the upvote/
un-upvote action, so a report that already sat at or above the threshold before this
feature shipped would otherwise never get its author notified — nobody has to touch its
upvotes again for that to happen. This migration runs the same rule once, historically,
against whatever data already exists, so "popular" is judged by current state, not by
whether someone happens to vote again after deploy.

Hand-rolled against the historical models rather than importing
notify_if_report_is_popular directly — Django migrations shouldn't depend on
application code that can change shape later.
"""

from django.conf import settings
from django.db import migrations
from django.db.models import Count


def backfill_popular_notifications(apps, schema_editor):
    Report = apps.get_model("reports", "Report")
    Notification = apps.get_model("notifications", "Notification")
    threshold = settings.POPULARITY_UPVOTE_THRESHOLD

    candidates = (
        Report.objects.filter(popular_notified=False, author__isnull=False)
        .annotate(upvote_count=Count("upvotes", distinct=True))
        .filter(upvote_count__gte=threshold)
    )
    for report in candidates:
        Notification.objects.create(recipient_id=report.author_id, report=report, kind="popular")
        report.popular_notified = True
        report.save(update_fields=["popular_notified"])


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_notification_kind"),
        ("reports", "0006_report_popular_notified"),
    ]

    operations = [
        migrations.RunPython(backfill_popular_notifications, migrations.RunPython.noop),
    ]
