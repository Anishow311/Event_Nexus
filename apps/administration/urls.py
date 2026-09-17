from django.urls import path
from . import views

urlpatterns = [
    path("", views.admin_dashboard, name="admin_dashboard"),
    path("clubs/<int:club_id>/approve/", views.approve_club, name="approve_club"),
    path("clubs/<int:club_id>/reject/", views.reject_club, name="reject_club"),
]
