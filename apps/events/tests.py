import datetime
from django.test import TestCase, Client
from django.urls import reverse
from apps.authentication.models import CustomUser, StudentProfile, ClubProfile
from apps.events.models import Event, Registration, CustomQuestion, QuestionOption, StudentAnswer


class CustomRsvpTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Club User and ClubProfile
        self.club_user = CustomUser.objects.create_user(
            email="techclub@campus.edu",
            password="password123",
            role="CLUB"
        )
        self.club_profile = ClubProfile.objects.create(
            user=self.club_user,
            club_name="Tech Club",
            category="Technical"
        )

        # Create Student User and StudentProfile
        self.student_user = CustomUser.objects.create_user(
            email="student@campus.edu",
            password="password123",
            role="STUDENT"
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            first_name="Jane",
            last_name="Doe"
        )

        # Create a Direct RSVP Event
        self.direct_event = Event.objects.create(
            club=self.club_profile,
            title="Intro to Python",
            description="A beginner workshop",
            date=datetime.date.today() + datetime.timedelta(days=3),
            time=datetime.time(14, 0),
            venue="Room 101",
            category="Technical",
            rsvp_mode="DIRECT"
        )

        # Create a Custom RSVP Event
        self.custom_event = Event.objects.create(
            club=self.club_profile,
            title="Hackathon 2026",
            description="Campus hackathon",
            date=datetime.date.today() + datetime.timedelta(days=7),
            time=datetime.time(9, 0),
            venue="Main Auditorium",
            category="Hackathon",
            rsvp_mode="CUSTOM"
        )

        # Add custom questions
        self.q_short = CustomQuestion.objects.create(
            event=self.custom_event,
            question_text="What is your GitHub username?",
            question_type="SHORT_ANSWER",
            is_required=True
        )
        self.q_mc = CustomQuestion.objects.create(
            event=self.custom_event,
            question_text="Select your T-shirt size",
            question_type="MULTIPLE_CHOICE",
            is_required=True
        )
        QuestionOption.objects.create(question=self.q_mc, option_text="M")
        QuestionOption.objects.create(question=self.q_mc, option_text="L")

        self.q_para = CustomQuestion.objects.create(
            event=self.custom_event,
            question_text="Any dietary restrictions?",
            question_type="PARAGRAPH",
            is_required=False
        )

    def test_direct_rsvp_post_registers_student(self):
        """DIRECT RSVP via POST creates a Registration instance and redirects back."""
        self.client.login(email="student@campus.edu", password="password123")
        url = reverse("rsvp_event", kwargs={"event_id": self.direct_event.id})
        response = self.client.post(url)

        # Should redirect
        self.assertEqual(response.status_code, 302)
        # Registration should exist
        self.assertTrue(
            Registration.objects.filter(
                student=self.student_profile,
                event=self.direct_event
            ).exists()
        )
        from apps.students.models import Notification
        self.assertTrue(
            Notification.objects.filter(
                student=self.student_profile,
                message=f"You have successfully registered for {self.direct_event.title}"
            ).exists()
        )

    def test_custom_rsvp_post_redirects_to_custom_rsvp_form(self):
        """When event has rsvp_mode='CUSTOM', main RSVP view redirects to custom_rsvp_form without registering."""
        self.client.login(email="student@campus.edu", password="password123")
        url = reverse("rsvp_event", kwargs={"event_id": self.custom_event.id})
        response = self.client.post(url)

        # Should redirect to custom_rsvp_form
        expected_url = reverse("custom_rsvp_form", kwargs={"event_id": self.custom_event.id})
        self.assertRedirects(response, expected_url)

        # Should NOT register yet
        self.assertFalse(
            Registration.objects.filter(
                student=self.student_profile,
                event=self.custom_event
            ).exists()
        )

    def test_custom_rsvp_form_get_renders_questions(self):
        """custom_rsvp_form GET request fetches custom questions and renders template."""
        self.client.login(email="student@campus.edu", password="password123")
        url = reverse("custom_rsvp_form", kwargs={"event_id": self.custom_event.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/rsvp_form.html")
        self.assertIn("questions", response.context)
        self.assertEqual(len(response.context["questions"]), 3)
        self.assertContains(response, "What is your GitHub username?")
        self.assertContains(response, "Select your T-shirt size")

    def test_custom_rsvp_form_post_creates_registration_and_answers(self):
        """custom_rsvp_form POST request creates Registration and saves StudentAnswer instances."""
        self.client.login(email="student@campus.edu", password="password123")
        url = reverse("custom_rsvp_form", kwargs={"event_id": self.custom_event.id})

        post_data = {
            f"question_{self.q_short.id}": "janedoe",
            f"question_{self.q_mc.id}": "M",
            f"question_{self.q_para.id}": "Vegetarian",
        }
        response = self.client.post(url, post_data)

        # Should redirect back to student dashboard with success message
        self.assertRedirects(response, reverse("student_dashboard"))

        # Registration should exist
        reg = Registration.objects.filter(
            student=self.student_profile,
            event=self.custom_event
        ).first()
        self.assertIsNotNone(reg)

        # StudentAnswers should be created and linked to Registration
        answers = StudentAnswer.objects.filter(registration=reg)
        self.assertEqual(answers.count(), 3)

        ans_short = answers.filter(question=self.q_short).first()
        self.assertEqual(ans_short.answer_text, "janedoe")

        ans_mc = answers.filter(question=self.q_mc).first()
        self.assertEqual(ans_mc.answer_text, "M")

        ans_para = answers.filter(question=self.q_para).first()
        self.assertEqual(ans_para.answer_text, "Vegetarian")

        from apps.students.models import Notification
        self.assertTrue(
            Notification.objects.filter(
                student=self.student_profile,
                message=f"You have successfully registered for {self.custom_event.title}"
            ).exists()
        )

    def test_custom_rsvp_form_missing_required_question(self):
        """Submitting custom RSVP form with missing required question displays error and does not register."""
        self.client.login(email="student@campus.edu", password="password123")
        url = reverse("custom_rsvp_form", kwargs={"event_id": self.custom_event.id})

        post_data = {
            f"question_{self.q_short.id}": "",  # Missing required field
            f"question_{self.q_mc.id}": "M",
        }
        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Registration.objects.filter(
                student=self.student_profile,
                event=self.custom_event
            ).exists()
        )

    def test_is_past_property(self):
        """Test event.is_past returns True for past dates and False for today and future dates."""
        past_event = Event.objects.create(
            club=self.club_profile,
            title="Old Event",
            description="Past event",
            date=datetime.date.today() - datetime.timedelta(days=2),
            time=datetime.time(10, 0),
            venue="Old Room",
            category="Technical",
            rsvp_mode="DIRECT"
        )
        today_event = Event.objects.create(
            club=self.club_profile,
            title="Today's Event",
            description="Happening today",
            date=datetime.date.today(),
            time=datetime.time(18, 0),
            venue="Room 202",
            category="Technical",
            rsvp_mode="DIRECT"
        )
        self.assertTrue(past_event.is_past)
        self.assertFalse(today_event.is_past)
        self.assertFalse(self.direct_event.is_past)

    def test_past_event_rsvp_blocked(self):
        """RSVP attempts for past events are blocked and do not create registrations."""
        self.client.login(email="student@campus.edu", password="password123")
        past_event = Event.objects.create(
            club=self.club_profile,
            title="Past Event",
            description="Expired event",
            date=datetime.date.today() - datetime.timedelta(days=1),
            time=datetime.time(10, 0),
            venue="Hall C",
            category="Technical",
            rsvp_mode="DIRECT"
        )
        url = reverse("rsvp_event", kwargs={"event_id": past_event.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Registration.objects.filter(
                student=self.student_profile,
                event=past_event
            ).exists()
        )


