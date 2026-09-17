import itertools
from django.shortcuts import render
from django.db.models import Q
from apps.core.decorators import student_required
from apps.events.models import Event
from apps.clubs.models import ClubPost, ClubMembership


@student_required
def student_dashboard(request):
    # 1. Fetch approved club memberships for privacy filter (only from verified clubs)
    approved_club_ids = []
    if request.user.is_authenticated:
        approved_club_ids = ClubMembership.objects.filter(
            student__user=request.user,
            status='approved',
            club__is_approved=True
        ).values_list('club_id', flat=True)

    # 2. Query events applying public/members-only filters and strictly is_approved=True
    events = Event.objects.filter(
        club__is_approved=True
    ).filter(
        Q(is_private=False) | Q(club_id__in=approved_club_ids)
    ).select_related('club').prefetch_related('likes').order_by('-created_at').distinct()

    # 3. Query posts applying public/members-only filters and strictly is_approved=True
    posts = ClubPost.objects.filter(
        club__is_approved=True
    ).filter(
        Q(is_private=False) | Q(club_id__in=approved_club_ids)
    ).select_related('club').prefetch_related('likes').order_by('-created_at').distinct()

    # 4. Use itertools.chain to merge both querysets into a single list
    # Sort strictly descending based on creation timestamp (newest item at index 0)
    timeline = sorted(
        itertools.chain(posts, events),
        key=lambda item: item.created_at,
        reverse=True
    )

    # 5. Package timeline, events, and posts into context dictionary
    context = {
        'timeline': timeline,
        'events': events,
        'posts': posts,
    }

    # 6. Render template
    return render(request, "students/dashboard.html", context)

