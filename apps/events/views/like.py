from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from apps.events.models import Event


@login_required
def toggle_like(request, event_id):
    """
    Toggle like/unlike on an Event for the authenticated user (Student or Club).
    Returns JSON with new like_count and is_liked status.
    """
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    if event.likes.filter(id=user.id).exists():
        event.likes.remove(user)
        is_liked = False
    else:
        event.likes.add(user)
        is_liked = True

    return JsonResponse({
        "success": True,
        "is_liked": is_liked,
        "like_count": event.likes.count(),
        "event_id": event.id,
    })
