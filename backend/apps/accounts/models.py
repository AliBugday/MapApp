from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.db import models


class Organization(models.Model):
    """A body allowed to post announcements and events.

    Two kinds: municipalities, and a broader institution/community catch-all covering
    ministries, universities, university clubs, and NGOs (e.g. Kızılay). Individual
    organizations within that catch-all are told apart on the map by their own logo
    (see Report.organization_logo_url), not by a finer-grained kind.
    """

    class Kind(models.TextChoices):
        MUNICIPALITY = "municipality", "Belediye"
        INSTITUTION = "institution", "Kurum / Topluluk"

    name = models.CharField(max_length=120, unique=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    # SET_NULL, matching User.organization below: deleting a ministry should orphan its
    # university, not cascade-delete it. Arbitrary depth is modelled here, but the UI only
    # ever renders one hop up (see ReportSerializer.organization_parent_name) — a full
    # recursive chain display is deferred until it's actually needed.
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def clean(self):
        # Admin is currently the only write path to Organization, and its ModelForm calls
        # full_clean() before saving — so this is the one guard standing between a careless
        # edit in the parent dropdown and an infinite loop the next time something walks
        # the chain (e.g. this same walk, or a future "full ancestry" display).
        super().clean()
        seen = {self.pk}
        node = self.parent
        depth = 0
        while node is not None:
            depth += 1
            if node.pk in seen or depth > 20:
                raise ValidationError("Bu üst kurum ataması bir döngü oluşturuyor.")
            seen.add(node.pk)
            node = node.parent


class User(AbstractUser):
    """Custom user model.

    Exists from the first migration because switching AUTH_USER_MODEL afterwards means
    rebuilding migration history.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    # Private — never exposed on any report or any other user's profile, only on this
    # user's own /api/auth/me/ response. geography=True for the same reason as
    # Report.location (apps/reports/models.py): distance lookups need real metres.
    home_location = gis_models.PointField(geography=True, srid=4326, null=True, blank=True)
    work_location = gis_models.PointField(geography=True, srid=4326, null=True, blank=True)
