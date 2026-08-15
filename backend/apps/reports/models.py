import io
from pathlib import Path

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps


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
    # Only meaningful for type=event; enforced in ReportSerializer.validate(), same reasoning
    # as visibility above.
    event_starts_at = models.DateTimeField(null=True, blank=True)
    event_ends_at = models.DateTimeField(null=True, blank=True)

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


class EventRSVP(models.Model):
    """One row per user per event report — same idempotency reasoning as Upvote: a row,
    not a counter, so a double-tap or a retried request cannot inflate the total.
    """

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="rsvps")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rsvps"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["report", "user"], name="unique_rsvp_per_user")
        ]

    def __str__(self):
        return f"{self.user_id} RSVPed to {self.report_id}"


class ReportImage(models.Model):
    """Separate model so a report can carry several photos later without a migration."""

    THUMBNAIL_SIZE = (128, 128)

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="reports/%Y/%m/")
    # Generated from `image` in save(), never accepted from the client. A phone photo is
    # commonly several MB; a map with dozens of pins each pulling in a full-size original
    # would make the page hang loading them. 128px covers both the pin (46px at 2x) and the
    # hover-card thumbnails, so this one derivative serves both.
    thumbnail = models.ImageField(upload_to="reports/thumbs/%Y/%m/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for report {self.report_id}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # `image` must be committed to storage before it can be reopened for thumbnailing,
        # so a first-time save writes the row twice: once for the upload, once for the
        # derived thumbnail.
        super().save(*args, **kwargs)
        if is_new and not self.thumbnail:
            filename = f"{Path(self.image.name).stem}_thumb.jpg"
            self.thumbnail.save(filename, self._make_thumbnail(), save=False)
            super().save(update_fields=["thumbnail"])

    def _make_thumbnail(self) -> ContentFile:
        self.image.open("rb")
        try:
            with Image.open(self.image) as source:
                # Phone cameras store rotation as EXIF metadata, not in the pixel data —
                # without this, thumbnails of portrait photos come out sideways.
                photo = ImageOps.exif_transpose(source).convert("RGB")
                photo = ImageOps.fit(photo, self.THUMBNAIL_SIZE, Image.LANCZOS)
                buffer = io.BytesIO()
                photo.save(buffer, format="JPEG", quality=80)
        finally:
            self.image.close()
        return ContentFile(buffer.getvalue())
