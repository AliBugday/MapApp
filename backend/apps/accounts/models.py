from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model.

    Deliberately identical to Django's default for now. It exists from the first
    migration because switching AUTH_USER_MODEL afterwards means rebuilding migration
    history. Future profile fields (home location, municipality affiliation) land here.
    """

    pass
