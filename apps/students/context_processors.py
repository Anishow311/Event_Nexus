from .models import Notification


def unread_notifications_count(request):
    """
    Context processor that returns the count of unread notifications
    for the currently authenticated student user.
    """
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        unread_count = Notification.objects.filter(
            student=request.user.student_profile,
            is_read=False
        ).count()
        return {'unread_notifications': unread_count}
    return {'unread_notifications': 0}
