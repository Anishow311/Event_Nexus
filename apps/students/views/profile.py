from django.shortcuts import render, redirect
from django.db.models import F
from apps.core.decorators import student_required
from apps.clubs.models import ClubMembership, ClubProfile


@student_required
def student_profile(request):
    profile = request.user.student_profile
    if request.method == "POST":
        profile.first_name = request.POST.get("first_name", profile.first_name).strip()
        profile.last_name = request.POST.get("last_name", profile.last_name).strip()
        profile.bio = request.POST.get("bio", profile.bio).strip()
        profile.major = request.POST.get("major", profile.major).strip()
        profile.class_of = request.POST.get("class_of", profile.class_of).strip()
        profile.interests = request.POST.get("interests", profile.interests).strip()
        profile.save()
        return redirect("student_profile")

    joined_clubs_count = ClubMembership.objects.filter(
        student=profile,
        status="approved"
    ).count()

    return render(request, "students/profile.html", {
        "profile": profile,
        "joined_clubs_count": joined_clubs_count,
    })


@student_required
def student_joined_clubs(request):
    profile = request.user.student_profile
    joined_clubs = ClubProfile.objects.filter(
        memberships__student=profile,
        memberships__status="approved"
    ).annotate(
        date_joined=F("memberships__created_at")
    ).select_related("user").distinct().order_by("club_name")

    return render(request, "students/joined_clubs.html", {
        "profile": profile,
        "joined_clubs": joined_clubs,
        "joined_clubs_count": joined_clubs.count(),
    })

