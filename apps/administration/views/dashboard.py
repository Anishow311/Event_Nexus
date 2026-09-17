from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.core.decorators import admin_required
from apps.authentication.models import StudentProfile, ClubProfile, CustomUser
from apps.events.models import Event


@admin_required
def admin_dashboard(request):
    """
    Primary administrative command center view displaying platform metrics,
    the pending club approval queue, and campus organization statuses.
    """
    total_students = StudentProfile.objects.count()
    total_clubs = ClubProfile.objects.filter(is_approved=True).count()
    total_events = Event.objects.count()
    total_users = CustomUser.objects.count()

    pending_clubs = (
        ClubProfile.objects.filter(is_approved=False)
        .select_related("user")
        .order_by("-id")
    )
    approved_clubs = (
        ClubProfile.objects.filter(is_approved=True)
        .select_related("user")
        .order_by("-id")
    )

    context = {
        "total_students": total_students,
        "total_clubs": total_clubs,
        "total_events": total_events,
        "total_users": total_users,
        "pending_clubs": pending_clubs,
        "approved_clubs": approved_clubs,
        "pending_count": pending_clubs.count(),
    }
    return render(request, "administration/dashboard.html", context)


@admin_required
def approve_club(request, club_id):
    """
    Approve an unverified club profile, unlocking full platform capabilities.
    """
    if request.method == "POST":
        club = get_object_or_404(ClubProfile, id=club_id)
        club.is_approved = True
        club.save()
        messages.success(request, f"Club '{club.club_name}' has been officially approved!")
    return redirect("admin_dashboard")


@admin_required
def reject_club(request, club_id):
    """
    Reject and remove an unapproved club organization registration.
    """
    if request.method == "POST":
        club = get_object_or_404(ClubProfile, id=club_id)
        club_name = club.club_name
        user = club.user

        # Deleting the user cascades and removes the associated ClubProfile
        if user:
            user.delete()
        else:
            club.delete()

        messages.warning(request, f"Club registration for '{club_name}' has been rejected and removed.")
    return redirect("admin_dashboard")
