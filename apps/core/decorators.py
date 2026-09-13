from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(required_roles):
    """
    Decorator for views that checks if the logged in user has one of the required roles.
    Accepts a single role string (e.g. 'STUDENT') or a list/tuple of roles.
    """
    if isinstance(required_roles, str):
        required_roles = [required_roles]

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            if request.user.role not in required_roles:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def student_required(view_func):
    return role_required("STUDENT")(view_func)


def club_required(view_func):
    return role_required("CLUB")(view_func)


def admin_required(view_func):
    return role_required("ADMIN")(view_func)
