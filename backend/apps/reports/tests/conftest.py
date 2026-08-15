"""Fixtures shared by the reports test modules.

These use force_authenticate rather than a real session login: the session flow itself is
already covered in apps/accounts/tests/test_auth.py, and repeating it here would only make
these tests slower without testing anything new.
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User

from .factories import create_organization

PASSWORD = "pw12345678"


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password=PASSWORD)


@pytest.fixture
def other_user(db):
    """A second user, for checking that one person's action isn't attributed to another."""
    return User.objects.create_user(username="somebody-else", password=PASSWORD)


@pytest.fixture
def org_user(db):
    """A member of an organization — can post announcement/event reports."""
    org = create_organization(name="Kadıköy Belediyesi")
    return User.objects.create_user(username="org-member", password=PASSWORD, organization=org)


@pytest.fixture
def other_org_user(db):
    """A member of a *different* organization — what makes the visibility tests meaningful."""
    org = create_organization(name="Üsküdar Belediyesi")
    return User.objects.create_user(
        username="other-org-member", password=PASSWORD, organization=org
    )


@pytest.fixture(autouse=True)
def _isolate_media_root(settings, tmp_path):
    """Image-upload tests write real files; without this override they'd land in the dev
    media volume instead of a throwaway per-test directory."""
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(client, user):
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def org_client(org_user):
    client = APIClient()
    client.force_authenticate(user=org_user)
    return client


@pytest.fixture
def other_org_client(other_org_user):
    client = APIClient()
    client.force_authenticate(user=other_org_user)
    return client
