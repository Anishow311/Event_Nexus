from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from apps.core.decorators import club_required
from apps.events.models import Event, Registration


@club_required
def event_attendees(request, event_id):
    """
    Renders the Attendees Dashboard for a specific event owned by the club.
    Fetches all associated Registration objects along with StudentProfile,
    User, and StudentAnswer data.
    """
    club_profile = getattr(request.user, 'club_profile', None)

    # Retrieve the event, ensuring ownership for security
    if club_profile:
        event = get_object_or_404(Event, id=event_id, club=club_profile)
    else:
        event = get_object_or_404(Event, id=event_id)

    # Fetch registrations with optimized prefetching and selecting
    registrations = (
        Registration.objects.filter(event=event)
        .select_related('student', 'student__user')
        .prefetch_related('answers', 'answers__question')
        .order_by('-registered_at')
    )

    context = {
        'event': event,
        'registrations': registrations,
        'total_attendees': registrations.count(),
    }
    return render(request, "events/attendees_list.html", context)
