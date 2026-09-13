from django.urls import path
from . import views

urlpatterns = [
    path("", views.club_dashboard, name="club_dashboard"),
    path("profile/", views.club_profile, name="club_profile"),
    path("profile/update/", views.update_club_profile, name="update_club_profile"),
    path("profile/<int:club_id>/", views.club_profile, name="club_profile_detail"),
    path("post/create/", views.create_post, name="create_post"),
    path("post/<int:post_id>/edit/", views.edit_post_view, name="edit_post"),
    path("post/<int:post_id>/delete/", views.delete_post, name="delete_post"),
    path("post/<int:post_id>/like/", views.toggle_post_like, name="toggle_post_like"),
    path("memberships/", views.memberships_list_view, name="memberships_list"),
    path("memberships/all/", views.memberships_list_view, name="club_memberships"),
    path("memberships/pending/", views.pending_requests_view, name="pending_requests"),
    path("memberships/process/", views.process_request_view, name="process_request"),
    path("memberships/process/<int:membership_id>/", views.process_request_view, name="process_request_with_id"),
    path("<int:club_id>/follow/", views.toggle_follow_club, name="toggle_follow_club"),
    path("follow/<int:club_id>/", views.toggle_follow_club),
    path("follow/", views.toggle_follow_club),
    path("<int:club_id>/request-membership/", views.request_membership, name="request_membership"),
    path("<int:club_id>/join/", views.request_membership, name="join_club"),
    path("request-membership/<int:club_id>/", views.request_membership),
    path("request-membership/", views.request_membership),
]



