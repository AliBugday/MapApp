"""Session-based authentication endpoints.

Sessions rather than tokens: Django and DRF already ship with everything needed, the
browser handles the cookie, and the Next.js proxy keeps the frontend on the same origin
so the cookie just works. No new dependency.
"""

from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


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
