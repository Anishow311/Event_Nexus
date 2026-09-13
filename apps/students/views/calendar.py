from django.shortcuts import render
from apps.core.decorators import student_required
from apps.events.models import Event


@student_required
def student_calendar(request):
    upcoming_events = Event.objects.all().order_by('date', 'time')
    context = {
        'events': upcoming_events
    }
    return render(request, "students/calendar.html", context)
