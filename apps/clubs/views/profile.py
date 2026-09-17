import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.decorators import club_required
from apps.authentication.models import ClubProfile
from apps.events.models import Event
from ..models import ClubPost, ClubMembership



@club_required
def club_profile(request, club_id=None):
    """
    Renders the club profile page.
    If club_id is provided, views that specific club.
    Otherwise, if logged in as a club, views their own profile.
    """
    if club_id:
        club = get_object_or_404(ClubProfile, id=club_id)
        is_owner = (request.user.role == 'CLUB' and hasattr(request.user, 'club_profile') and request.user.club_profile == club)
    else:
        if request.user.role == 'CLUB' and hasattr(request.user, 'club_profile'):
            club = request.user.club_profile
            is_owner = True
        else:
            # Fallback for students viewing general club page if no id specified
            club = ClubProfile.objects.first()
            is_owner = False

    is_following = False
    user_membership = None
    if request.user.is_authenticated and club:
        is_following = club.followers.filter(id=request.user.id).exists()
        if hasattr(request.user, 'student_profile'):
            user_membership = ClubMembership.objects.filter(
                club=club,
                student=request.user.student_profile
            ).first()

    is_member = (user_membership.status == 'approved') if user_membership else False

    # Members-Only Visibility Logic:
    # If the user is an approved member or the club owner, show all posts and events.
    # Otherwise, filter to only public items (is_private=False).
    if is_owner or is_member:
        events = Event.objects.filter(club=club).order_by('-created_at') if club else Event.objects.none()
        posts = ClubPost.objects.filter(club=club).order_by('-created_at') if club else ClubPost.objects.none()
    else:
        events = Event.objects.filter(club=club, is_private=False).order_by('-created_at') if club else Event.objects.none()
        posts = ClubPost.objects.filter(club=club, is_private=False).order_by('-created_at') if club else ClubPost.objects.none()

    followers_count = club.followers.count() if club else 0
    members_count = ClubMembership.objects.filter(club=club, status='approved').count() if club else 0
    events_count = events.count() if club else 0

    context = {
        "club": club,
        "is_owner": is_owner,
        "events": events,
        "posts": posts,
        "followers_count": followers_count,
        "members_count": members_count,
        "events_count": events_count,
        # Backward compatibility aliases
        "follower_count": followers_count,
        "member_count": members_count,
        "is_following": is_following,
        "user_membership": user_membership,
        "membership_status": user_membership.status if user_membership else None,
        "is_pending": (user_membership.status == 'pending') if user_membership else False,
        "is_member": (user_membership.status == 'approved') if user_membership else False,
    }
    return render(request, "clubs/profile.html", context)



@club_required
def toggle_follow_club(request, club_id=None):
    """
    Toggle follow/unfollow for the authenticated user on a ClubProfile.
    Checks if request.user is in club.followers.all().
    If yes, removes user. If no, adds user.
    Returns JsonResponse with is_followed and follower_count.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=405)

    target_id = club_id or request.POST.get("club_id")
    if not target_id and request.body:
        try:
            body_data = json.loads(request.body.decode("utf-8"))
            target_id = body_data.get("club_id")
        except Exception:
            pass

    if not target_id:
        return JsonResponse({"error": "Club ID is required."}, status=400)

    club = get_object_or_404(ClubProfile, id=target_id)
    user = request.user

    if user in club.followers.all():
        club.followers.remove(user)
        is_followed = False
    else:
        club.followers.add(user)
        is_followed = True

    new_count = club.followers.count()
    return JsonResponse({
        "success": True,
        "is_followed": is_followed,
        "follower_count": new_count,
        "followers_count": new_count,
    })



@club_required
def update_club_profile(request):
    """
    Handles POST requests from the Edit Profile modal.
    Updates text fields and uploads new logo if provided.
    """
    if request.method == "POST":
        # Ensure the logged-in user is a club account with a profile
        if request.user.role != 'CLUB' or not hasattr(request.user, 'club_profile'):
            messages.error(request, "Unauthorized access. Only clubs can update their profile.")
            return redirect('club_dashboard')

        club = request.user.club_profile

        # 1. Update text fields with a safety net for 'None' values!
        club.club_name = (request.POST.get('club_name') or club.club_name or "").strip()
        club.bio = (request.POST.get('bio') or club.bio or "").strip()
        club.category = (request.POST.get('category') or club.category or "").strip()
        club.contact_email = (request.POST.get('contact_email') or club.contact_email or "").strip()

        # 2. Check if a new logo image was uploaded
        if 'logo' in request.FILES:
            club.logo = request.FILES['logo']

        # 3. Save changes (Django & Cloudinary handle the upload automatically)
        club.save()

        messages.success(request, "Club profile updated successfully!")
        return redirect(request.META.get('HTTP_REFERER', 'club_profile'))

    return redirect('club_profile')
