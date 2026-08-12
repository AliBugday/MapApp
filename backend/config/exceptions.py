from django.http import Http404
from rest_framework.exceptions import NotFound
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    """DRF's own handler forwards Django's Http404 message as-is — e.g. "No Report
    matches the given query." — which stays in English regardless of LANGUAGE_CODE
    because get_object_or_404 builds it with plain string formatting, never gettext.
    Dropping that message and letting NotFound fall back to its own (translated)
    default_detail keeps every 404 in the configured language.
    """
    if isinstance(exc, Http404):
        exc = NotFound()
    return drf_exception_handler(exc, context)
