from django.urls import path
from . import views

urlpatterns = [
    path("", views.student_dashboard, name="student_dashboard"),
    path("profile/", views.student_profile, name="student_profile"),
    path("explore/", views.explore, name="explore"),
    path("calendar/", views.student_calendar, name="student_calendar"),
    path("notifications/", views.student_notifications, name="notifications"),
    path("registrations/", views.my_registrations, name="my_registrations"),
    path("settings/", views.student_settings, name="student_settings"),
    path("feed/new/", views.fetch_new_feed_items, name="fetch_new_feed_items"),
]

