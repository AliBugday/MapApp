"""Fixtures shared by the reports test modules.

These use force_authenticate rather than a real session login: the session flow itself is
already covered in apps/accounts/tests/test_auth.py, and repeating it here would only make
these tests slower without testing anything new.
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User

PASSWORD = "pw12345678"


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password=PASSWORD)


@pytest.fixture
def other_user(db):
    """A second user, for checking that one person's action isn't attributed to another."""
    return User.objects.create_user(username="somebody-else", password=PASSWORD)


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(client, user):
    client.force_authenticate(user=user)
    return client
