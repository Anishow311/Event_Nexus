from django.urls import path
from . import views

urlpatterns = [
    path("", views.admin_dashboard, name="admin_dashboard"),
    path("clubs/<int:club_id>/approve/", views.approve_club, name="approve_club"),
    path("clubs/<int:club_id>/reject/", views.reject_club, name="reject_club"),
    path("clubs/<int:club_id>/remove/", views.remove_club, name="remove_club"),
    path("students/", views.manage_students, name="manage_students"),
    path("students/<int:user_id>/remove/", views.remove_student, name="remove_student"),
    path("events/", views.manage_events, name="manage_events"),
]
