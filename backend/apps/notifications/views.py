from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """GET lists, POST marks all read — one URL for both, same shape ReportViewSet.comments
    already uses for combining GET+POST. Unlike reports, GET is not public here: these are
    a user's own private notifications, so IsAuthenticated applies to both methods.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = request.user.notifications.select_related("report")[:50]
        return Response(NotificationSerializer(queryset, many=True).data)

    def post(self, request):
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
