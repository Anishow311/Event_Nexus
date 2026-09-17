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
    """
    Decorator for views that checks if the logged in user has the CLUB role
    and their club profile is approved by an administrator.
    If not approved, redirects them to 'clubs:pending_approval'.
    Allows non-club users (Students/Admins) only on shared public views with target parameters.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        # 1. Soft-lock check: ANY user with CLUB role must be approved
        if request.user.role == "CLUB":
            club_profile = getattr(request.user, "clubprofile", None) or getattr(request.user, "club_profile", None)
            if not club_profile or not getattr(club_profile, "is_approved", False):
                return redirect("clubs:pending_approval")
            return view_func(request, *args, **kwargs)

        # 2. For non-club users, permit public club interaction endpoints if targeting a specific entity
        if (
            "club_id" in kwargs
            or "club_id" in request.POST
            or ("post_id" in kwargs and view_func.__name__ == "toggle_post_like")
        ):
            return view_func(request, *args, **kwargs)

        # 3. For all other dedicated club organizer views, restrict strictly to CLUB role
        raise PermissionDenied

    return wrapper


def admin_required(view_func):
    return role_required("ADMIN")(view_func)
