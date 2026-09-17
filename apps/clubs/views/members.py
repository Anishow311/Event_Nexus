import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from apps.core.decorators import club_required
from apps.authentication.models import ClubProfile, StudentProfile
from ..models import ClubMembership



@club_required
def memberships_list_view(request):
    """
    Fetches all ClubMembership objects for the logged-in club where status is 'approved',
    calculates active and pending counts, supports search filtering via ?q=, and renders clubs/memberships.html.
    """
    club = request.user.club_profile
    approved_memberships = (
        ClubMembership.objects.filter(club=club, status="approved")
        .select_related("student", "student__user")
        .order_by("-created_at")
    )

    active_count = approved_memberships.count()
    pending_count = ClubMembership.objects.filter(club=club, status="pending").count()

    search_query = request.GET.get("q", "").strip()
    if search_query:
        memberships = approved_memberships.filter(
            Q(student__first_name__icontains=search_query)
            | Q(student__last_name__icontains=search_query)
            | Q(student__user__email__icontains=search_query)
        )
    else:
        memberships = approved_memberships

    return render(
        request,
        "clubs/memberships.html",
        {
            "club": club,
            "memberships": memberships,
            "active_count": active_count,
            "approved_count": active_count,
            "pending_count": pending_count,
            "search_query": search_query,
        },
    )



@club_required
def pending_requests_view(request):
    """
    Fetches all ClubMembership objects for the logged-in club where status is 'pending'
    and renders clubs/pending_requests.html.
    """
    club = request.user.club_profile
    pending_requests = (
        ClubMembership.objects.filter(club=club, status="pending")
        .select_related("student", "student__user")
        .order_by("-created_at")
    )
    approved_count = ClubMembership.objects.filter(club=club, status="approved").count()

    return render(
        request,
        "clubs/pending_requests.html",
        {
            "club": club,
            "pending_requests": pending_requests,
            "pending_count": pending_requests.count(),
            "approved_count": approved_count,
        },
    )


@club_required
def process_request_view(request, membership_id=None):
    """
    Accepts a POST request with the membership ID and an action ('approve' or 'reject')
    to update the status in the database.
    """
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("pending_requests")

    target_id = request.POST.get("membership_id") or membership_id
    action = request.POST.get("action", "").strip().lower()

    if not target_id:
        messages.error(request, "Membership ID is required.")
        return redirect("pending_requests")

    club = request.user.club_profile
    membership = get_object_or_404(ClubMembership, id=target_id, club=club)
    student_name = f"{membership.student.first_name} {membership.student.last_name}".strip() or membership.student.user.email

    if action == "approve":
        membership.status = "approved"
        membership.save()
        messages.success(request, f"Application for {student_name} has been approved successfully!")
    elif action == "reject":
        membership.status = "rejected"
        membership.save()
        messages.info(request, f"Application for {student_name} has been rejected.")
    else:
        messages.error(request, "Invalid action specified. Must be 'approve' or 'reject'.")

    return redirect("pending_requests")


# Backwards compatibility alias
membership_requests = pending_requests_view



@club_required
def request_membership(request, club_id=None):
    """
    POST endpoint that uses get_or_create on the ClubMembership model
    for the request.user (via their StudentProfile) and the specified club with status='pending'.
    Returns a JsonResponse indicating success.
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

    # Disallow club owners from requesting membership to their own club
    if user.role == 'CLUB' and hasattr(user, 'club_profile') and user.club_profile == club:
        return JsonResponse({"error": "You are the manager of this club."}, status=400)

    # Obtain or ensure StudentProfile for the user
    if hasattr(user, 'student_profile'):
        student_profile = user.student_profile
    else:
        first_name = user.first_name or (user.email.split('@')[0] if user.email else 'Student')
        last_name = user.last_name or ''
        student_profile, _ = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
            }
        )

    membership, created = ClubMembership.objects.get_or_create(
        student=student_profile,
        club=club,
        defaults={'status': 'pending'}
    )

    # If previously rejected or modified, reset to pending upon re-request
    if not created and membership.status == 'rejected':
        membership.status = 'pending'
        membership.save()

    return JsonResponse({
        "success": True,
        "status": membership.status,
        "created": created,
        "message": "Membership request submitted successfully." if created or membership.status == 'pending' else f"Membership status: {membership.status}"
    })


