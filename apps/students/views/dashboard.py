from django.shortcuts import render
from django.db.models import Q
from apps.core.decorators import student_required
from apps.events.models import Event
from apps.clubs.models import ClubPost, ClubMembership


@student_required
def student_dashboard(request):
    # 1. Fetch all events, sorted by newest first
    events = Event.objects.select_related('club').prefetch_related('likes').order_by('-created_at')

    # 2. Query database for posts with privacy security check:
    # Only fetch posts where is_private=False OR request.user is an approved member of the post's club
    approved_club_ids = []
    if request.user.is_authenticated:
        approved_club_ids = ClubMembership.objects.filter(
            student__user=request.user,
            status='approved'
        ).values_list('club_id', flat=True)

    posts = ClubPost.objects.filter(
        Q(is_private=False) | Q(club_id__in=approved_club_ids)
    ).select_related('club').prefetch_related('likes').order_by('-created_at').distinct()

    # 3. Package events and posts into context dictionary
    context = {
        'events': events,
        'posts': posts,
    }

    # 4. Render template
    return render(request, "students/dashboard.html", context)
