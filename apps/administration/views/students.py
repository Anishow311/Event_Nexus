from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.core.decorators import admin_required
from apps.authentication.models import StudentProfile, CustomUser


@admin_required
def manage_students(request):
    """
    Administrative view to manage all registered students.
    Fetches all student profiles with their core user accounts.
    """
    students = StudentProfile.objects.all().select_related("user").order_by("-id")
    context = {
        "students": students,
        "total_students": students.count(),
    }
    return render(request, "administration/manage_students.html", context)


@admin_required
def remove_student(request, user_id):
    """
    Accepts POST requests to remove a student by their core user ID.
    Calls .delete() on the CustomUser model to cascade-delete all related student records.
    """
    if request.method == "POST":
        user_to_delete = get_object_or_404(CustomUser, id=user_id)
        if user_to_delete == request.user:
            messages.error(request, "You cannot delete your own administrative account.")
            return redirect("manage_students")

        student_name = (
            f"{user_to_delete.student_profile.first_name} {user_to_delete.student_profile.last_name}"
            if hasattr(user_to_delete, "student_profile")
            else user_to_delete.email
        )
        user_to_delete.delete()
        messages.success(request, f"Student account '{student_name}' and all associated records have been removed.")

    return redirect("manage_students")
