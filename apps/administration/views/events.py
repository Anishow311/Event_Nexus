from django.shortcuts import render
from django.utils import timezone
from apps.core.decorators import admin_required
from apps.events.models import Event


@admin_required
def manage_events(request):
    """
    Administrative view to manage all campus events.
    Queries all events with hosting club details and orders by date descending.
    Provides current date for conditional color-coded timeline rendering in the template.
    """
    events = Event.objects.all().select_related("club").order_by("-date")
    today = timezone.now().date()
    context = {
        "events": events,
        "today": today,
        "total_events": events.count(),
    }
    return render(request, "administration/manage_events.html", context)
