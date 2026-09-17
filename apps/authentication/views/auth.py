from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from apps.authentication.forms import RegistrationForm, LoginForm
from apps.authentication.models import CustomUser, StudentProfile, ClubProfile
from apps.authentication.supabase_client import get_supabase_client


def home(request):
    """
    Traffic controller / Smart redirect for root URL (/).
    Directs authenticated users to their corresponding dashboards based on role,
    and unauthenticated users to the login page.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    user = request.user
    if user.is_superuser or getattr(user, "role", None) == "ADMIN":
        return redirect("admin_dashboard")
    elif getattr(user, "role", None) == "CLUB":
        return redirect("club_dashboard")
    elif getattr(user, "role", None) == "STUDENT":
        return redirect("student_dashboard")

    return redirect("login")


def logout_view(request):
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
    except Exception:
        pass
    logout(request)
    return redirect("login")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            password = form.cleaned_data["password"]
            role = form.cleaned_data["role"]
            first_name = form.cleaned_data.get("first_name", "")
            last_name = form.cleaned_data.get("last_name", "")
            club_name = form.cleaned_data.get("club_name", "")

            # 1. Authenticate / Register user in Supabase
            try:
                supabase = get_supabase_client()
                response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "role": role,
                            "first_name": first_name,
                            "last_name": last_name,
                            "club_name": club_name,
                        }
                    }
                })

                if not response.user:
                    form.add_error(None, "Could not create user with Supabase. Please try again.")
                    return render(request, "authentication/register.html", {"form": form})

            except Exception as e:
                error_msg = getattr(e, "message", str(e))
                form.add_error(None, f"Supabase registration error: {error_msg}")
                return render(request, "authentication/register.html", {"form": form})

            # 2. Persist user & profile in database
            user = form.save(commit=False)
            user.email = email
            user.set_password(password)
            user.save()

            if user.role == "STUDENT":
                StudentProfile.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                )
                if response.session:
                    request.session["supabase_access_token"] = response.session.access_token
                    request.session["supabase_refresh_token"] = response.session.refresh_token
                    login(request, user)
                    return redirect("student_dashboard")
                else:
                    messages.success(request, "Account created! If email confirmation is enabled, please verify your email before logging in.")
                    return redirect("login")

            elif user.role == "CLUB":
                ClubProfile.objects.create(
                    user=user,
                    club_name=club_name,
                )
                if response.session:
                    request.session["supabase_access_token"] = response.session.access_token
                    request.session["supabase_refresh_token"] = response.session.refresh_token
                    login(request, user)
                    return redirect("club_dashboard")
                else:
                    messages.success(request, "Account created! If email confirmation is enabled, please verify your email before logging in.")
                    return redirect("login")

    else:
        form = RegistrationForm()

    return render(request, "authentication/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            password = form.cleaned_data["password"]

            # 1. First, check local Django authentication (supports Django superusers, staff, and local accounts)
            local_user = authenticate(request, email=email, password=password) or authenticate(request, username=email, password=password)
            if not local_user:
                candidate_user = CustomUser.objects.filter(email__iexact=email).first()
                if candidate_user and candidate_user.check_password(password):
                    local_user = candidate_user

            if local_user:
                login(request, local_user)

                # Optional: Sync session with Supabase in the background if possible, but do not block login
                try:
                    supabase = get_supabase_client()
                    response = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    if response and response.session:
                        request.session["supabase_access_token"] = response.session.access_token
                        request.session["supabase_refresh_token"] = response.session.refresh_token
                except Exception:
                    pass

                if local_user.role == "STUDENT":
                    return redirect("student_dashboard")
                elif local_user.role == "CLUB":
                    return redirect("club_dashboard")
                elif local_user.role == "ADMIN" or local_user.is_superuser:
                    return redirect("admin_dashboard")
                return redirect("home")

            # 2. If not matched locally, authenticate via Supabase Auth
            try:
                supabase = get_supabase_client()
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                if not response.user:
                    form.add_error(None, "Invalid email or password.")
                    return render(request, "authentication/login.html", {"form": form})

                # 3. Find or synchronize local Django user
                user = CustomUser.objects.filter(email__iexact=email).first()
                if not user:
                    user_metadata = response.user.user_metadata or {}
                    role = user_metadata.get("role", "STUDENT")
                    user = CustomUser.objects.create(
                        email=email,
                        role=role
                    )
                    user.set_password(password)
                    user.save()

                    if role == "STUDENT":
                        StudentProfile.objects.get_or_create(
                            user=user,
                            defaults={
                                "first_name": user_metadata.get("first_name", ""),
                                "last_name": user_metadata.get("last_name", "")
                            }
                        )
                    elif role == "CLUB":
                        ClubProfile.objects.get_or_create(
                            user=user,
                            defaults={
                                "club_name": user_metadata.get("club_name", "")
                            }
                        )
                else:
                    if not user.check_password(password):
                        user.set_password(password)
                        user.save()

                # Store tokens in Django session
                if response.session:
                    request.session["supabase_access_token"] = response.session.access_token
                    request.session["supabase_refresh_token"] = response.session.refresh_token

                login(request, user)

                if user.role == "STUDENT":
                    return redirect("student_dashboard")
                elif user.role == "CLUB":
                    return redirect("club_dashboard")
                elif user.role == "ADMIN" or user.is_superuser:
                    return redirect("admin_dashboard")
                return redirect("home")

            except Exception as e:
                error_msg = getattr(e, "message", str(e))
                form.add_error(None, f"Login failed: {error_msg}")

    else:
        form = LoginForm()

    return render(request, "authentication/login.html", {"form": form})
