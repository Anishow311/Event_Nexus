from django.shortcuts import render
from apps.core.decorators import student_required
from apps.events.models import Registration




@student_required
def my_registrations(request):
    student_profile = request.user.student_profile
    registrations = Registration.objects.filter(student=student_profile).select_related('event').order_by('-registered_at')
    return render(request, "students/my_registrations.html", {"registrations": registrations})


@student_required
def student_settings(request):
    return render(request, "students/settings.html")
