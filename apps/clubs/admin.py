from django.contrib import admin
from .models import ClubPost, ClubMembership


@admin.register(ClubPost)
class ClubPostAdmin(admin.ModelAdmin):
    list_display = ("club", "content", "created_at")
    list_filter = ("created_at", "club")
    search_fields = ("content", "club__club_name")


@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = ("student", "club", "status", "created_at")
    list_filter = ("status", "created_at", "club")
    search_fields = ("student__first_name", "student__last_name", "student__user__email", "club__club_name")

