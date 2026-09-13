from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.core.decorators import club_required
from apps.events.models import Event


@club_required
def edit_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id, club=request.user.club_profile)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category = request.POST.get("category", "").strip()
        venue = request.POST.get("venue", "").strip()
        date = request.POST.get("date")
        time = request.POST.get("time")
        total_seats = request.POST.get("total_seats")
        rsvp_mode = request.POST.get("rsvp_mode")

        if not (title and description and category and venue and date and time):
            messages.error(request, "Please fill in all required fields.")
            return redirect(request.META.get("HTTP_REFERER", "club_dashboard"))

        event.title = title
        event.description = description
        event.category = category
        event.venue = venue
        event.date = date
        event.time = time

        if total_seats:
            try:
                event.total_seats = int(total_seats)
            except ValueError:
                pass
        else:
            event.total_seats = None

        if rsvp_mode:
            event.rsvp_mode = rsvp_mode

        is_private = request.POST.get("is_private") in ["true", "on", "1", True]
        event.is_private = is_private
        event.is_public = not is_private

        if "image" in request.FILES and request.FILES["image"]:
            event.image = request.FILES["image"]

        event.save()
        messages.success(request, f"Event '{event.title}' updated successfully!")
        return redirect(request.META.get("HTTP_REFERER", "club_dashboard"))

    return redirect("club_dashboard")


# Alias for convenience
edit_event = edit_event_view


@club_required
def delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id, club=request.user.club_profile)
    title = event.title
    event.delete()
    messages.success(request, f"Event '{title}' deleted successfully.")
    return redirect(request.META.get("HTTP_REFERER", "club_dashboard"))


# Alias for convenience
delete_event = delete_event_view
