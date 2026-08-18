from django.urls import path
from . import views

urlpatterns = [
    path("student/", views.student_dashboard, name="student_dashboard"),
    path("club/", views.club_dashboard, name="club_dashboard"),
    path("admin/", views.admin_dashboard, name="admin_dashboard"),
    path("student/profile/", views.student_profile, name="student_profile"),
    path("student/explore/", views.explore, name="explore"),
    path("student/notifications/", views.notifications, name="notifications"),
    path("student/registrations/", views.my_registrations, name="my_registrations"),
    path("student/calendar/", views.student_calendar, name="student_calendar"),
    path("student/settings/", views.student_settings, name="student_settings"),
]