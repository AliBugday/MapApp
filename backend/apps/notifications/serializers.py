from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    report_id = serializers.IntegerField(source="report.id", read_only=True)
    report_title = serializers.CharField(source="report.title", read_only=True)
    report_type = serializers.CharField(source="report.type", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "report_id",
            "report_title",
            "report_type",
            "kind",
            "is_read",
            "created_at",
        ]
