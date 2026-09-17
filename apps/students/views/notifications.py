from django.shortcuts import render
from apps.core.decorators import student_required
from apps.students.models import Notification


@student_required
def student_notifications(request):
    """
    Fetches all notifications for the logged-in student ordered by newest first,
    marks unread notifications as read, and renders students/notifications.html.
    """
    student_profile = request.user.student_profile
    notifications_qs = Notification.objects.filter(student=student_profile).order_by('-created_at')

    # Convert to list before updating so template retains initial read/unread state
    notifications_list = list(notifications_qs)

    # Update unread notifications to is_read = True
    Notification.objects.filter(student=student_profile, is_read=False).update(is_read=True)

    return render(request, "students/notifications.html", {"notifications": notifications_list})


# Alias for backward compatibility with existing urls/imports
notifications = student_notifications
