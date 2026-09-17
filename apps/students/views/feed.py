import itertools
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from apps.core.decorators import student_required
from apps.clubs.models import ClubPost, ClubMembership
from apps.events.models import Event


@student_required
def fetch_new_feed_items(request):
    """
    Accepts GET parameter latest_timestamp.
    Queries Posts and Events created strictly after latest_timestamp,
    applying the same public/members-only privacy filters.
    Merges and sorts items in descending order of created_at (newest first).
    Returns the items rendered as an HTML string.
    """
    latest_timestamp_str = request.GET.get("latest_timestamp")
    if not latest_timestamp_str:
        return HttpResponse("", content_type="text/html")

    # Parse ISO 8601 or numeric timestamp
    ts = parse_datetime(latest_timestamp_str)
    if ts is None:
        try:
            val = float(latest_timestamp_str)
            if val > 1e11:  # Millisecond timestamp
                val /= 1000.0
            ts = datetime.fromtimestamp(val, tz=timezone.get_current_timezone())
        except (ValueError, OSError):
            return HttpResponseBadRequest("Invalid timestamp format.")

    # Approved club memberships for members-only privacy security filter
    approved_club_ids = []
    if request.user.is_authenticated:
        approved_club_ids = ClubMembership.objects.filter(
            student__user=request.user,
            status="approved",
            club__is_approved=True
        ).values_list("club_id", flat=True)

    # Query for posts created strictly after latest_timestamp from approved clubs
    posts = ClubPost.objects.filter(
        club__is_approved=True,
        created_at__gt=ts
    ).filter(
        Q(is_private=False) | Q(club_id__in=approved_club_ids)
    ).select_related("club").prefetch_related("likes").distinct()

    # Query for events created strictly after latest_timestamp from approved clubs
    events = Event.objects.filter(
        club__is_approved=True,
        created_at__gt=ts
    ).filter(
        Q(is_private=False) | Q(club_id__in=approved_club_ids)
    ).select_related("club").prefetch_related("likes").distinct()

    # Merge and sort descending (newest item at index 0)
    timeline = sorted(
        itertools.chain(posts, events),
        key=lambda item: item.created_at,
        reverse=True
    )

    # Render template partial as HTML string
    return render(request, "students/partials/feed_items.html", {"timeline": timeline})
