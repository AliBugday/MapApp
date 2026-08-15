"""Shared test data helpers.

Kept in a plain module rather than conftest.py because these are a constant and a
function, not fixtures — importing them explicitly is clearer than pytest injection.
"""

import io

from django.contrib.gis.geos import Point
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.accounts.models import Organization
from apps.reports.models import Report

# Istanbul, roughly Sultanahmet.
ISTANBUL = {"latitude": 41.0082, "longitude": 28.9784}


def create_report(**kwargs):
    defaults = {
        "title": "Broken streetlight",
        "location": Point(ISTANBUL["longitude"], ISTANBUL["latitude"], srid=4326),
    }
    return Report.objects.create(**{**defaults, **kwargs})


def create_organization(**kwargs):
    defaults = {"name": "Test Belediyesi", "kind": Organization.Kind.MUNICIPALITY}
    return Organization.objects.create(**{**defaults, **kwargs})


def uploaded_image(name="photo.jpg", size=(400, 300), color=(180, 40, 40)):
    """An in-memory JPEG, generated rather than committed as a binary fixture."""
    buffer = io.BytesIO()
    Image.new("RGB", size, color=color).save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")
