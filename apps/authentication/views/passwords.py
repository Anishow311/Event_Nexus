from django.shortcuts import render, redirect
from django.contrib import messages
from apps.authentication.forms import ForgotPasswordForm, ResetPasswordForm
from apps.authentication.supabase_client import get_supabase_client


def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            try:
                supabase = get_supabase_client()
                redirect_url = request.build_absolute_uri("/reset-password/")
                supabase.auth.reset_password_for_email(
                    email,
                    {"redirect_to": redirect_url}
                )
                messages.success(request, f"Password reset instructions have been sent to {email}.")
                return render(request, "authentication/verify_email.html", {"email": email, "type": "reset"})
            except Exception as e:
                error_msg = getattr(e, "message", str(e))
                form.add_error(None, f"Could not send reset email: {error_msg}")
    else:
        form = ForgotPasswordForm()

    return render(request, "authentication/forgot_password.html", {"form": form})


def reset_password(request):
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["password"]
            token = request.POST.get("access_token") or request.session.get("supabase_access_token")
            try:
                supabase = get_supabase_client()
                if token:
                    supabase.auth.set_session(token, "")
                supabase.auth.update_user({"password": new_password})
                
                if request.user.is_authenticated:
                    request.user.set_password(new_password)
                    request.user.save()

                messages.success(request, "Your password has been successfully reset. Please log in with your new password.")
                return redirect("login")
            except Exception as e:
                error_msg = getattr(e, "message", str(e))
                form.add_error(None, f"Password reset failed: {error_msg}")
    else:
        form = ResetPasswordForm()

    return render(request, "authentication/reset_password.html", {"form": form})
