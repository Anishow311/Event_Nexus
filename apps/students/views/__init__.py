from .dashboard import student_dashboard
from .profile import student_profile
from .calendar import student_calendar
from .explore import explore
from .activity import my_registrations, student_settings
from .notifications import student_notifications, notifications
from .feed import fetch_new_feed_items

__all__ = [
    "student_dashboard",
    "student_profile",
    "student_calendar",
    "explore",
    "student_notifications",
    "notifications",
    "my_registrations",
    "student_settings",
    "fetch_new_feed_items",
]

