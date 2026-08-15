from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis_models
from django.db import models


class Organization(models.Model):
    """A government body allowed to post announcements and events.

    Kept to municipality/public-institution kinds only — this demo is framed around
    government organizations, not private companies.
    """

    class Kind(models.TextChoices):
        MUNICIPALITY = "municipality", "Belediye"
        PUBLIC = "public", "Kamu kurumu"

    name = models.CharField(max_length=120, unique=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


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
