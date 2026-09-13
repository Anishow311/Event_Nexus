from django.shortcuts import render
from django.db.models import Q
from apps.core.decorators import student_required
from apps.authentication.models import ClubProfile
from apps.events.models import Event
from apps.clubs.models import ClubMembership


@student_required
def explore(request):
    query = request.GET.get('q', '')

    if query.strip():
        # Filter ClubProfile: search query in name OR description (case-insensitive)
        # Note: In the database model, name maps to `club_name` and description to `bio`
        club_q = Q(club_name__icontains=query) | Q(bio__icontains=query)
        if hasattr(ClubProfile, "name"):
            club_q |= Q(name__icontains=query)
        if hasattr(ClubProfile, "description"):
            club_q |= Q(description__icontains=query)
        clubs = ClubProfile.objects.filter(club_q)

        # Filter Event: search query in title OR description OR location/venue (case-insensitive)
        # Note: In the database model, location maps to `venue`
        event_q = Q(title__icontains=query) | Q(description__icontains=query)
        if hasattr(Event, "venue"):
            event_q |= Q(venue__icontains=query)
        if hasattr(Event, "location"):
            event_q |= Q(location__icontains=query)
        events = Event.objects.filter(event_q)

        # Crucial Privacy Check for Events:
        # Ensure is_private=False OR request.user is an approved member of the event's hosting club
        approved_club_ids = []
        if request.user.is_authenticated:
            approved_club_ids = ClubMembership.objects.filter(
                student__user=request.user,
                status='approved'
            ).values_list('club_id', flat=True)

        events = events.filter(
            Q(is_private=False) | Q(club_id__in=approved_club_ids)
        ).select_related('club').prefetch_related('likes').distinct()
    else:
        clubs = ClubProfile.objects.none()
        events = Event.objects.none()

    context = {
        'query': query,
        'clubs': clubs,
        'events': events,
    }
    return render(request, "students/explore.html", context)
