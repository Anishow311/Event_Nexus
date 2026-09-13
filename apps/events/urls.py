from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_event, name="create_event"),
    path("<int:event_id>/edit/", views.edit_event_view, name="edit_event"),
    path("<int:event_id>/delete/", views.delete_event_view, name="delete_event"),
    path("rsvp/<int:event_id>/", views.rsvp_event, name="rsvp_event"),
    path("custom-rsvp/<int:event_id>/", views.custom_rsvp_form, name="custom_rsvp_form"),
    path("<int:event_id>/custom-rsvp/", views.custom_rsvp_form),
    path("<int:event_id>/attendees/", views.event_attendees, name="event_attendees"),
    path("event/<int:event_id>/attendees/", views.event_attendees),
    path("<int:event_id>/like/", views.toggle_like, name="toggle_like"),
    path("like/<int:event_id>/", views.toggle_like),
]



