"""Shared test data helpers.

Kept in a plain module rather than conftest.py because these are a constant and a
function, not fixtures — importing them explicitly is clearer than pytest injection.
"""

from django.contrib.gis.geos import Point

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
