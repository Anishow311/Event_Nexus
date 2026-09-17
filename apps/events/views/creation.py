import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from apps.core.decorators import club_required
from apps.events.models import Event, CustomQuestion, QuestionOption
from apps.students.models import Notification


@club_required
def create_event(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category = request.POST.get("category", "").strip()
        venue = request.POST.get("venue", "").strip()
        date = request.POST.get("date")
        time = request.POST.get("time")
        total_seats = request.POST.get("total_seats")
        rsvp_mode = request.POST.get("rsvp_mode", "DIRECT")
        image = request.FILES.get("image")
        is_private = request.POST.get("is_private") in ["true", "on", "1", True]

        club_profile = request.user.club_profile

        if not (title and description and category and venue and date and time):
            messages.error(request, "Please fill in all required fields.")
            return render(request, "events/create_event.html")

        try:
            with transaction.atomic():
                # 1. Create and save the Event object first to obtain event.id
                event = Event(
                    club=club_profile,
                    title=title,
                    description=description,
                    category=category,
                    venue=venue,
                    date=date,
                    time=time,
                    rsvp_mode=rsvp_mode,
                    is_public=not is_private,
                    is_private=is_private,
                )

                if total_seats:
                    try:
                        event.total_seats = int(total_seats)
                    except ValueError:
                        pass

                if image:
                    event.image = image

                event.save()

                # If event is members-only, notify all approved club members
                if is_private:
                    approved_memberships = club_profile.memberships.filter(
                        status="approved"
                    ).select_related("student")
                    notifications = [
                        Notification(
                            student=membership.student,
                            message=f"New members-only update from {club_profile.club_name}: {event.title}",
                        )
                        for membership in approved_memberships
                    ]
                    if notifications:
                        Notification.objects.bulk_create(notifications)

                # 2. If RSVP mode is CUSTOM, process and save custom questions & options
                if rsvp_mode == "CUSTOM":
                    custom_questions_raw = request.POST.get("custom_questions_json") or request.POST.get("custom_questions") or "[]"
                    try:
                        questions_data = json.loads(custom_questions_raw)
                        if isinstance(questions_data, list):
                            for q_item in questions_data:
                                q_text = q_item.get("question_text", "").strip()
                                if not q_text:
                                    continue
                                q_type = q_item.get("question_type", "SHORT_ANSWER")
                                is_req = bool(q_item.get("is_required", True))

                                # Create CustomQuestion linked to the new event via event.id
                                question = CustomQuestion.objects.create(
                                    event=event,
                                    question_text=q_text,
                                    question_type=q_type,
                                    is_required=is_req
                                )

                                # If MULTIPLE_CHOICE, save options into QuestionOption table
                                if q_type == "MULTIPLE_CHOICE":
                                    options_data = q_item.get("options", [])
                                    # Support list/array format as well as comma-separated string fallback
                                    if isinstance(options_data, list):
                                        options_list = [str(opt).strip() for opt in options_data if str(opt).strip()]
                                    elif isinstance(options_data, str):
                                        options_list = [opt.strip() for opt in options_data.split(",") if opt.strip()]
                                    else:
                                        options_list = []

                                    for opt_text in options_list:
                                        QuestionOption.objects.create(
                                            question=question,
                                            option_text=opt_text
                                        )
                    except (json.JSONDecodeError, TypeError, KeyError, ValueError):
                        pass

            messages.success(request, f"Event '{title}' created and published successfully!")
            return redirect("club_dashboard")

        except Exception as e:
            messages.error(request, f"An error occurred while creating the event: {str(e)}")
            return render(request, "events/create_event.html")

    return render(request, "events/create_event.html")


