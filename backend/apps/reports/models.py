from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models


class Report(models.Model):
    """A civic issue or request pinned to a geographic point."""

    class Status(models.TextChoices):
        # Stored values (left) stay in English — they're an API/DB contract, not UI text.
        # Only the human-readable label (right, used by the Django admin) is Turkish.
        OPEN = "open", "Açık"
        IN_PROGRESS = "in_progress", "İşlemde"
        RESOLVED = "resolved", "Çözüldü"
        REJECTED = "rejected", "Reddedildi"

    class Type(models.TextChoices):
        ISSUE = "issue", "Sorun / Şikayet"
        REQUEST = "request", "Talep"
        ANNOUNCEMENT = "announcement", "Duyuru"
        EVENT = "event", "Etkinlik"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Herkese açık"
        MEMBERS = "members", "Yalnızca üyelere"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.ISSUE)
    # Only meaningful for announcement/event; enforced in ReportSerializer.validate() rather
    # than here so the rule can name the offending field in a 400 instead of failing a
    # database constraint.
    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC
    )

    # geography=True so distance lookups are in metres on a sphere. With a plain
    # geometry column at SRID 4326, distances come back in degrees, which makes
    # "reports within 2 km" quietly wrong.
    # spatial_index defaults to True, so GeoDjango creates the GiST index for us.
    location = gis_models.PointField(geography=True, srid=4326)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on {self.report_id}"


class Upvote(models.Model):
    """One row per user per report.

    Modelled as a row rather than a counter so a double-tap or a retried request
    cannot inflate the total.
    """

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="upvotes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="upvotes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["report", "user"], name="unique_upvote_per_user")
        ]

    def __str__(self):
        return f"{self.user_id} upvoted {self.report_id}"


class ReportImage(models.Model):
    """Separate model so a report can carry several photos later without a migration."""

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="reports/%Y/%m/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for report {self.report_id}"
