"""Session-based authentication endpoints.

Sessions rather than tokens: Django and DRF already ship with everything needed, the
browser handles the cookie, and the Next.js proxy keeps the frontend on the same origin
so the cookie just works. No new dependency.
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.gis.geos import Point
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LocationUpdateSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Signing the new user straight in saves a pointless second round trip.
        #
        # login() needs to know which backend authenticated the user. authenticate() sets
        # that attribute, but we never called it, so login() falls back to the single
        # entry in AUTHENTICATION_BACKENDS. Adding a second backend would make this raise
        # ValueError — call authenticate() first if that ever happens.
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, **serializer.validated_data)
        if user is None:
            # One message for both a wrong username and a wrong password, so the response
            # can't be used to discover which usernames exist.
            return Response(
                {"detail": "Kullanıcı adı veya şifre hatalı."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MeView(APIView):
    """Who is signed in — the frontend calls this once on load.

    Always 200, with {"user": null} when anonymous rather than 401: this is a question,
    not a protected resource, so the frontend's first render has no error path to handle.

    The response is wrapped in a "user" key instead of returning a bare null because
    DRF's JSONRenderer turns None into a zero-byte body, which is not valid JSON and
    makes response.json() throw in the browser.

    ensure_csrf_cookie is the important part. DRF's SessionAuthentication only enforces
    CSRF once it has found a session user, so an anonymous login POST is never blocked —
    the case that breaks is a *returning* visitor with a live session cookie but no
    csrftoken cookie, whose next POST (logout, or creating a report) would 403. Calling
    this endpoint on page load guarantees the cookie is there.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        return Response({"user": UserSerializer(user).data if user else None})

    def patch(self, request):
        """Set or clear the signed-in user's home/work location.

        permission_classes stays AllowAny at the class level (GET must work for
        anonymous), so the auth check is inline here instead — same shape already used in
        apps/reports/views.py's permission classes.
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = LocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if "home" in serializer.validated_data:
            home = serializer.validated_data["home"]
            user.home_location = (
                Point(home["longitude"], home["latitude"], srid=4326) if home else None
            )
        if "work" in serializer.validated_data:
            work = serializer.validated_data["work"]
            user.work_location = (
                Point(work["longitude"], work["latitude"], srid=4326) if work else None
            )
        user.save()
        return Response({"user": UserSerializer(user).data})
