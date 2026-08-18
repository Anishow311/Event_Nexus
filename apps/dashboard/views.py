from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from apps.events.models import Event  # <-- NEW: We imported your Event model!

def role_required(required_role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied

            if request.user.role != required_role:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


@role_required("STUDENT")
def student_dashboard(request):
    # 1. Ask the database for all events, sorted by newest first
    events = Event.objects.all().order_by('-created_at')
    
    # 2. Package the events into a "context" dictionary
    context = {
        'events': events
    }
    
    # 3. Send the package along with the HTML file
    return render(request, "dashboard/student_dashboard.html", context)


@role_required("CLUB")
def club_dashboard(request):
    return render(request, "dashboard/club_dashboard.html")


@role_required("ADMIN")
def admin_dashboard(request):
    return render(request, "dashboard/admin_dashboard.html")

@role_required("STUDENT")
def student_profile(request):
    return render(request, "dashboard/student_profile.html")

@role_required("STUDENT")
def explore(request):
    return render(request, "dashboard/explore.html")

@role_required("STUDENT")
def notifications(request):
    return render(request, "dashboard/notifications.html")

@role_required("STUDENT")
def my_registrations(request):
    return render(request, "dashboard/my_registrations.html")

@role_required("STUDENT")
def student_calendar(request):
    return render(request, "dashboard/calendar.html")

@role_required("STUDENT")
def student_settings(request):
    return render(request, "dashboard/settings.html")