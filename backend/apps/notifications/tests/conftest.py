import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.reports.tests.factories import create_organization

PASSWORD = "pw12345678"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password=PASSWORD)


@pytest.fixture
def other_user(db):
    """A second user, for checking that one person's notifications aren't another's."""
    return User.objects.create_user(username="somebody-else", password=PASSWORD)


@pytest.fixture
def auth_client(client, user):
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def org_user(db):
    """A member of an organization — can post the event reports these tests trigger on."""
    org = create_organization(name="Kadıköy Belediyesi")
    return User.objects.create_user(username="org-member", password=PASSWORD, organization=org)


@pytest.fixture
def org_client(org_user):
    client = APIClient()
    client.force_authenticate(user=org_user)
    return client
