from django.conf import settings
from django.db import models


class Notification(models.Model):
    """A notification about one report, sent to one recipient.

    Still no actor/verb fields — the two kinds below (nearby report, popular report) are
    both fully described by {kind, report, recipient}, so a generic actor/verb shape
    would add nothing yet. Revisit if a third kind needs more than that.
    """

    class Kind(models.TextChoices):
        NEARBY = "nearby", "Yakınınızda"
        POPULAR = "popular", "Popüler oluyor"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    report = models.ForeignKey("reports.Report", on_delete=models.CASCADE)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.NEARBY)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.recipient_id} about {self.report_id}"
