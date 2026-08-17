import pytest

from .factories import create_report, uploaded_image


@pytest.mark.django_db
def test_organization_logo_url_null_for_author_without_org(auth_client, user):
    create_report(author=user)

    response = auth_client.get("/api/reports/")

    assert response.data["results"][0]["organization_logo_url"] is None


@pytest.mark.django_db
def test_organization_logo_url_null_when_org_has_no_logo(org_client, org_user):
    create_report(author=org_user)

    response = org_client.get("/api/reports/")

    assert response.data["results"][0]["organization_logo_url"] is None


@pytest.mark.django_db
def test_organization_logo_url_present_when_uploaded(org_client, org_user):
    org_user.organization.logo = uploaded_image(name="logo.png")
    org_user.organization.save()
    create_report(author=org_user)

    response = org_client.get("/api/reports/")

    logo_url = response.data["results"][0]["organization_logo_url"]
    assert logo_url is not None
    assert "/media/organizations/" in logo_url
