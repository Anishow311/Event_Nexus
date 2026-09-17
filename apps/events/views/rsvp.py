from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from apps.events.models import Event, Registration, CustomQuestion, QuestionOption, StudentAnswer
from apps.students.models import Notification


@login_required
def rsvp_event(request, event_id):
    """
    Handles event RSVP / registration for students and allows the event host/owner club
    to view the RSVP list (attendees) without being blocked by 403 Forbidden errors.
    """
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    # Safely determine the club profile for the user and host/club for the event
    user_club = getattr(user, 'club_profile', None) or getattr(user, 'clubprofile', None)
    event_club = getattr(event, 'club', None) or getattr(event, 'host', None)

    # Ownership check: Compare user/club against the event's owner/host
    is_owner = False
    if user_club and event_club and user_club == event_club:
        is_owner = True
    elif event_club and getattr(event_club, 'user', None) == user:
        is_owner = True
    elif getattr(event, 'host', None) == user:
        is_owner = True
    elif user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
        is_owner = True

    # If the user is the event owner/club, render the RSVP list (attendees dashboard)
    if is_owner:
        registrations = (
            Registration.objects.filter(event=event)
            .select_related('student', 'student__user')
            .prefetch_related('answers', 'answers__question')
            .order_by('-registered_at')
        )
        context = {
            'event': event,
            'registrations': registrations,
            'total_attendees': registrations.count(),
        }
        return render(request, "events/attendees_list.html", context)

    # If user is a student, proceed with student RSVP registration
    if user.role == 'STUDENT' or hasattr(user, 'student_profile'):
        if getattr(event, 'club', None) and not event.club.is_approved:
            messages.error(request, "This event belongs to a club that is pending administrative approval.")
            return redirect(request.META.get('HTTP_REFERER', 'student_dashboard'))

        if event.is_past:
            messages.warning(request, f"'{event.title}' has already ended. RSVP is closed.")
            return redirect(request.META.get('HTTP_REFERER', 'student_dashboard'))

        if event.rsvp_mode == 'DISABLED':
            messages.warning(request, f"RSVP is currently disabled for '{event.title}'.")
            return redirect(request.META.get('HTTP_REFERER', 'student_dashboard'))

        student_profile = getattr(user, 'student_profile', None)
        if not student_profile:
            messages.error(request, "Student profile could not be found.")
            return redirect(request.META.get('HTTP_REFERER', 'student_dashboard'))

        # Check if already registered
        if Registration.objects.filter(student=student_profile, event=event).exists():
            messages.info(request, f"You are already registered for '{event.title}'.")
            return redirect(request.META.get('HTTP_REFERER', 'student_dashboard'))

        # Check RSVP Mode
        if event.rsvp_mode == 'CUSTOM':
            # Do not register yet. Redirect to custom RSVP form view
            return redirect('custom_rsvp_form', event_id=event.id)

        # DIRECT RSVP: Create Registration instance and redirect back
        registration, created = Registration.objects.get_or_create(
            student=student_profile,
            event=event
        )

        if created:
            Notification.objects.create(
                student=student_profile,
                message=f"You have successfully registered for {event.title}"
            )
            messages.success(request, f"Successfully registered for '{event.title}'!")
        else:
            messages.info(request, f"You are already registered for '{event.title}'.")

        return redirect(request.META.get('HTTP_REFERER', 'student_dashboard'))

    # If user is a different club (not the owner), deny permission
    raise PermissionDenied("You do not have permission to view or RSVP to this event.")


@login_required
def custom_rsvp_form(request, event_id):
    """
    Handles rendering (GET) and processing (POST) of custom questions for events
    with rsvp_mode='CUSTOM'.
    """
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    # Verify student identity
    student_profile = getattr(user, 'student_profile', None)
    if not student_profile:
        messages.error(request, "Only students can register for events.")
        return redirect(request.META.get('HTTP_REFERER', 'student_dashboard'))

    # Check if event has ended
    if event.is_past:
        messages.warning(request, f"'{event.title}' has already ended. Registration is closed.")
        return redirect('student_dashboard')

    # Check if RSVP is disabled
    if getattr(event, 'club', None) and not event.club.is_approved:
        messages.error(request, "This event belongs to a club that is pending administrative approval.")
        return redirect('student_dashboard')

    if event.rsvp_mode == 'DISABLED':
        messages.warning(request, f"RSVP is currently disabled for '{event.title}'.")
        return redirect('student_dashboard')

    # Check if student is already registered
    if Registration.objects.filter(student=student_profile, event=event).exists():
        messages.info(request, f"You are already registered for '{event.title}'.")
        return redirect('student_dashboard')

    # GET: Fetch event.custom_questions.all() and render rsvp_form.html
    if request.method == "GET":
        # If event is DIRECT without custom questions, redirect to standard rsvp
        if event.rsvp_mode == 'DIRECT' and not event.custom_questions.exists():
            return redirect('rsvp_event', event_id=event.id)

        questions = event.custom_questions.prefetch_related('options').all()
        context = {
            'event': event,
            'questions': questions,
        }
        return render(request, "events/rsvp_form.html", context)

    # POST: Create Registration and capture StudentAnswer records
    if request.method == "POST":
        questions = event.custom_questions.prefetch_related('options').all()

        # Validate required questions before persisting
        missing_required = []
        for question in questions:
            if question.is_required:
                ans_val = request.POST.get(f"question_{question.id}") or request.POST.get(str(question.id))
                ans_list = request.POST.getlist(f"question_{question.id}") or request.POST.getlist(str(question.id))
                has_val = (ans_val and str(ans_val).strip()) or any(str(x).strip() for x in ans_list)
                if not has_val:
                    missing_required.append(question.question_text)

        if missing_required:
            messages.error(
                request,
                f"Please answer the following required question(s): {', '.join(missing_required)}"
            )
            return render(request, "events/rsvp_form.html", {
                'event': event,
                'questions': questions,
            })

        # Save Registration and StudentAnswer instances atomically
        with transaction.atomic():
            registration, created = Registration.objects.get_or_create(
                student=student_profile,
                event=event
            )

            # Loop through the questions to capture answers from POST data
            for question in questions:
                ans_list = request.POST.getlist(f"question_{question.id}") or request.POST.getlist(str(question.id))
                ans_val = request.POST.get(f"question_{question.id}") or request.POST.get(str(question.id))

                if len(ans_list) > 1:
                    answer_text = ", ".join([str(v).strip() for v in ans_list if str(v).strip()])
                elif ans_val is not None and str(ans_val).strip():
                    answer_text = str(ans_val).strip()
                elif ans_list and str(ans_list[0]).strip():
                    answer_text = str(ans_list[0]).strip()
                else:
                    answer_text = ""

                if answer_text:
                    StudentAnswer.objects.create(
                        registration=registration,
                        question=question,
                        answer_text=answer_text
                    )

            # Also check any other POST data matching question_<id> that might not have been caught
            processed_q_ids = {q.id for q in questions}
            for key, value in request.POST.items():
                if key.startswith("question_"):
                    try:
                        raw_id = int(key.replace("question_", ""))
                        if raw_id not in processed_q_ids and value and str(value).strip():
                            cq = event.custom_questions.filter(id=raw_id).first()
                            if cq:
                                StudentAnswer.objects.create(
                                    registration=registration,
                                    question=cq,
                                    answer_text=str(value).strip()
                                )
                                processed_q_ids.add(raw_id)
                    except ValueError:
                        pass

            if created:
                Notification.objects.create(
                    student=student_profile,
                    message=f"You have successfully registered for {event.title}"
                )

        messages.success(request, f"Successfully registered for '{event.title}'!")
        return redirect('student_dashboard')
