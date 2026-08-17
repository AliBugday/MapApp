import pytest

from apps.accounts.models import Organization, User

from .conftest import PASSWORD
from .factories import create_organization, create_report


@pytest.mark.django_db
def test_organization_parent_name_present_for_child_org(client):
    university = create_organization(name="Hacettepe Üniversitesi")
    club = create_organization(name="HÜ Dağcılık Kulübü", parent=university)
    author = User.objects.create_user(username="club-member", password=PASSWORD, organization=club)
    create_report(author=author)

    response = client.get("/api/reports/")

    assert response.data["results"][0]["organization_name"] == "HÜ Dağcılık Kulübü"
    assert response.data["results"][0]["organization_parent_name"] == "Hacettepe Üniversitesi"


@pytest.mark.django_db
def test_organization_parent_name_null_for_top_level_org(org_client, org_user):
    create_report(author=org_user)

    response = org_client.get("/api/reports/")

    assert response.data["results"][0]["organization_name"] is not None
    assert response.data["results"][0]["organization_parent_name"] is None


@pytest.mark.django_db
def test_organization_parent_name_null_for_author_without_org(auth_client, user):
    create_report(author=user)

    response = auth_client.get("/api/reports/")

    assert response.data["results"][0]["organization_name"] is None
    assert response.data["results"][0]["organization_parent_name"] is None


@pytest.mark.django_db
def test_direct_self_parent_is_rejected():
    org = create_organization(name="Kızılay")
    org.parent = org

    with pytest.raises(Exception):
        org.full_clean()


@pytest.mark.django_db
def test_three_level_cycle_is_rejected():
    a = create_organization(name="A", kind=Organization.Kind.INSTITUTION)
    b = create_organization(name="B", kind=Organization.Kind.INSTITUTION, parent=a)
    c = create_organization(name="C", kind=Organization.Kind.INSTITUTION, parent=b)
    a.parent = c

    with pytest.raises(Exception):
        a.full_clean()
