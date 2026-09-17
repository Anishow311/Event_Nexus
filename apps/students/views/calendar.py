import json
from django.shortcuts import render
from apps.core.decorators import student_required
from apps.events.models import Event


@student_required
def student_calendar(request):
    # Fetch all Event objects the student has RSVP'd to (via registrations)
    rsvp_events = Event.objects.filter(
        registrations__student__user=request.user
    ).distinct().order_by('date', 'time')

    # Format into a dictionary: { 'YYYY-MM-DD': [{'title': ..., 'time': ..., 'venue': ...}, ...] }
    events_by_date = {}
    for event in rsvp_events:
        date_str = event.date.strftime('%Y-%m-%d')
        # Formatted 12-hour time e.g. "7:00 PM"
        formatted_time = event.time.strftime('%I:%M %p').lstrip('0') if event.time else ''
        if formatted_time.startswith(':'):
            formatted_time = '12' + formatted_time

        event_data = {
            'id': event.id,
            'title': event.title,
            'time': formatted_time,
            'venue': event.venue,
        }

        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(event_data)

    events_json = json.dumps(events_by_date)

    context = {
        'events': rsvp_events,
        'events_json': events_json,
    }
    return render(request, "students/calendar.html", context)

