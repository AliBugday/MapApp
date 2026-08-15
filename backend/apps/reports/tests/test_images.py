import pytest
from PIL import Image

from apps.reports.models import ReportImage

from .factories import create_report, uploaded_image


@pytest.mark.django_db
def test_upload_attaches_to_the_correct_report_and_generates_a_thumbnail(auth_client, user):
    report = create_report(author=user)

    response = auth_client.post(
        f"/api/reports/{report.id}/images/", {"image": uploaded_image()}, format="multipart"
    )

    assert response.status_code == 201
    report_image = ReportImage.objects.get(id=response.data["id"])
    assert report_image.report_id == report.id
    with Image.open(report_image.thumbnail) as thumb:
        assert thumb.size == ReportImage.THUMBNAIL_SIZE


@pytest.mark.django_db
def test_upload_by_a_non_author_is_403(auth_client, other_user):
    report = create_report(author=other_user)

    response = auth_client.post(
        f"/api/reports/{report.id}/images/", {"image": uploaded_image()}, format="multipart"
    )

    assert response.status_code == 403
    assert ReportImage.objects.count() == 0


@pytest.mark.django_db
def test_upload_without_a_file_is_400(auth_client, user):
    report = create_report(author=user)

    response = auth_client.post(f"/api/reports/{report.id}/images/", {}, format="multipart")

    assert response.status_code == 400


@pytest.mark.django_db
def test_images_appear_in_the_report_response(client, user):
    report = create_report(author=user)
    ReportImage.objects.create(report=report, image=uploaded_image())

    response = client.get(f"/api/reports/{report.id}/")

    assert len(response.data["images"]) == 1
    assert response.data["images"][0]["url"].startswith("/media/")
    assert response.data["images"][0]["thumbnail_url"].startswith("/media/")
