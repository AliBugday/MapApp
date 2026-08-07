from django.contrib.gis import admin

from .models import Comment, Report, ReportImage, Upvote


@admin.register(Report)
class ReportAdmin(admin.GISModelAdmin):
    list_display = ["title", "status", "author", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "description"]


admin.site.register(Comment)
admin.site.register(Upvote)
admin.site.register(ReportImage)
