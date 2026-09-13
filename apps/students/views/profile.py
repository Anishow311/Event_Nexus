from django.shortcuts import render, redirect
from apps.core.decorators import student_required


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

    return render(request, "students/profile.html", {"profile": profile})
