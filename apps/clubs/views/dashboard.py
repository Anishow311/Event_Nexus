from django.shortcuts import render, redirect
from django.utils import timezone
from apps.core.decorators import club_required
from apps.events.models import Event
from ..models import ClubPost, ClubMembership


def pending_approval(request):
    """
    Landing view for clubs awaiting administrator approval.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    club_profile = getattr(request.user, "clubprofile", None) or getattr(request.user, "club_profile", None)
    if club_profile and getattr(club_profile, "is_approved", False):
        return redirect("club_dashboard")

    return render(request, "clubs/pending_approval.html", {
        "club": club_profile,
    })



@club_required
def club_dashboard(request):
    club = request.user.club_profile
    events = Event.objects.filter(club=club).order_by('-created_at')
    posts = ClubPost.objects.filter(club=club).order_by('-created_at')
    active_count = ClubMembership.objects.filter(club=club, status='approved').count()
    pending_count = ClubMembership.objects.filter(club=club, status='pending').count()

    followers_count = club.followers.count()
    events_count = events.count()
    upcoming_events_count = events.filter(date__gte=timezone.now().date()).count()

    return render(request, "clubs/dashboard.html", {
        "events": events,
        "posts": posts,
        "club": club,
        "active_count": active_count,
        "pending_count": pending_count,
        "followers_count": followers_count,
        "events_count": events_count,
        "upcoming_events_count": upcoming_events_count,
        # Backward compatibility aliases
        "member_count": active_count,
        "pending_requests_count": pending_count,
        "total_followers": followers_count,
        "events_hosted": events_count,
        "upcoming_count": upcoming_events_count,
    })

