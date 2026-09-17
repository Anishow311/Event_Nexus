from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.decorators import club_required
from apps.students.models import Notification
from ..models import ClubPost



@club_required
def create_post(request):
    if request.method == "POST":
        content = request.POST.get("content", "").strip()

        if not content:
            messages.error(request, "Announcement content is required.")
            return redirect("club_dashboard")

        image = request.FILES.get("image")
        is_private = request.POST.get("is_private") in ["true", "on", "1", True]

        post = ClubPost(
            club=request.user.club_profile,
            content=content,
            is_private=is_private,
        )
        if image:
            post.image = image

        post.save()

        # Members-only notification trigger for approved club members
        if is_private:
            approved_memberships = request.user.club_profile.memberships.filter(
                status="approved"
            ).select_related("student")
            post_title = (post.content[:50] + "...") if len(post.content) > 50 else post.content
            notifications = [
                Notification(
                    student=membership.student,
                    message=f"New members-only update from {request.user.club_profile.club_name}: {post_title}",
                )
                for membership in approved_memberships
            ]
            if notifications:
                Notification.objects.bulk_create(notifications)

        messages.success(request, "Announcement published successfully!")
        return redirect("club_dashboard")

    return render(request, "clubs/create_post.html")


@club_required
def edit_post_view(request, post_id):
    post = get_object_or_404(ClubPost, id=post_id, club=request.user.club_profile)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()

        if not content:
            messages.error(request, "Announcement content is required.")
            return redirect(request.META.get("HTTP_REFERER", "club_dashboard"))

        post.content = content
        post.is_private = request.POST.get("is_private") in ["true", "on", "1", True]

        if "image" in request.FILES and request.FILES["image"]:
            post.image = request.FILES["image"]

        post.save()
        messages.success(request, "Announcement updated successfully!")
        return redirect(request.META.get("HTTP_REFERER", "club_dashboard"))

    return redirect("club_dashboard")


# Alias for convenience
edit_post = edit_post_view


@club_required
def delete_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(ClubPost, id=post_id, club=request.user.club_profile)
        post.delete()
        messages.success(request, "Announcement deleted successfully.")
    return redirect(request.META.get("HTTP_REFERER", "club_dashboard"))


@club_required
def toggle_post_like(request, post_id):
    """
    Toggle like/unlike on a ClubPost for the authenticated user (Student or Club).
    Returns JSON with new like_count and is_liked status.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=405)

    post = get_object_or_404(ClubPost, id=post_id)
    user = request.user

    if user in post.likes.all():
        post.likes.remove(user)
        is_liked = False
    else:
        post.likes.add(user)
        is_liked = True

    return JsonResponse({
        "success": True,
        "is_liked": is_liked,
        "like_count": post.likes.count(),
        "post_id": post.id,
    })




