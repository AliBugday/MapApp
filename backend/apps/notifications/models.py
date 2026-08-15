from django.conf import settings
from django.db import models


class Notification(models.Model):
    """A single "an Etkinlik happened near you" notification.

    No actor/verb fields: this app has exactly one notification kind (a nearby event),
    and inventing a generic shape for kinds that don't exist yet would be designing for
    a hypothetical requirement. Add them when a second kind actually needs them.
    """

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    report = models.ForeignKey("reports.Report", on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.recipient_id} about {self.report_id}"
