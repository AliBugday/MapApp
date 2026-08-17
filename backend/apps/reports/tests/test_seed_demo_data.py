import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import Organization
from apps.notifications.models import Notification
from apps.reports.management.commands import seed_demo_data
from apps.reports.models import Report, ReportImage

from .factories import uploaded_image


@pytest.fixture
def photo_dir(tmp_path, monkeypatch):
    """Points the command at a throwaway directory with one fixture photo under a real
    seeded filename, so a photo attaches deterministically regardless of which (if any)
    real photos the user has downloaded into the actual seed_data/photos folder."""
    photos = tmp_path / "photos"
    photos.mkdir()
    (photos / "kaldirim-cukur.jpg").write_bytes(uploaded_image().read())
    monkeypatch.setattr(seed_demo_data, "PHOTO_DIR", photos)
    return photos


@pytest.mark.django_db
def test_seed_creates_expected_reports(photo_dir):
    call_command("seed_demo_data")

    assert Report.objects.count() == 28
    assert Organization.objects.filter(parent__isnull=False).exists()
    assert ReportImage.objects.exists()
    assert Notification.objects.count() == 0


@pytest.mark.django_db
def test_rerun_without_flush_raises(photo_dir):
    call_command("seed_demo_data")

    with pytest.raises(CommandError):
        call_command("seed_demo_data")


@pytest.mark.django_db
def test_flush_reseeds_without_deleting_organizations_or_their_logos(photo_dir):
    call_command("seed_demo_data")
    org = Organization.objects.get(name="Ankara Büyükşehir Belediyesi")
    org.logo = uploaded_image(name="abb-logo.png")
    org.save()
    organization_count_before = Organization.objects.count()

    call_command("seed_demo_data", flush=True)

    assert Organization.objects.count() == organization_count_before
    org.refresh_from_db()
    assert org.logo
    assert Report.objects.count() == 28
