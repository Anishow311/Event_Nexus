import json
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from apps.authentication.models import CustomUser, StudentProfile, ClubProfile
from apps.events.models import Event, Registration


class StudentCalendarViewTests(TestCase):
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

        # Create another student
        self.other_student_user = CustomUser.objects.create_user(
            email="other@campus.edu",
            password="password123",
            role="STUDENT"
        )
        self.other_student_profile = StudentProfile.objects.create(
            user=self.other_student_user,
            first_name="John",
            last_name="Smith"
        )

        # Event 1: RSVP'd by student
        self.event1 = Event.objects.create(
            club=self.club_profile,
            title="Intro to Python",
            description="A beginner workshop",
            date=datetime.date(2026, 9, 20),
            time=datetime.time(14, 30),
            venue="Room 101",
            category="Technical"
        )
        Registration.objects.create(student=self.student_profile, event=self.event1)

        # Event 2: RSVP'd by student on same day
        self.event2 = Event.objects.create(
            club=self.club_profile,
            title="Python Advanced",
            description="Deep dive",
            date=datetime.date(2026, 9, 20),
            time=datetime.time(16, 0),
            venue="Lab 3",
            category="Technical"
        )
        Registration.objects.create(student=self.student_profile, event=self.event2)

        # Event 3: RSVP'd only by other student
        self.event3 = Event.objects.create(
            club=self.club_profile,
            title="Design Thinking",
            description="UI/UX workshop",
            date=datetime.date(2026, 9, 25),
            time=datetime.time(10, 0),
            venue="Hall B",
            category="Design"
        )
        Registration.objects.create(student=self.other_student_profile, event=self.event3)

    def test_student_calendar_redirects_unauthenticated(self):
        response = self.client.get(reverse('student_calendar'))
        self.assertEqual(response.status_code, 302)

    def test_student_calendar_rsvp_events_and_json(self):
        self.client.login(email="student@campus.edu", password="password123")
        response = self.client.get(reverse('student_calendar'))
        self.assertEqual(response.status_code, 200)

        # Verify events in context
        events = list(response.context['events'])
        self.assertIn(self.event1, events)
        self.assertIn(self.event2, events)
        self.assertNotIn(self.event3, events)

        # Verify events_json in context
        events_json = response.context['events_json']
        self.assertIsInstance(events_json, str)
        parsed_events = json.loads(events_json)

        date_key = "2026-09-20"
        self.assertIn(date_key, parsed_events)
        self.assertEqual(len(parsed_events[date_key]), 2)

        event1_data = parsed_events[date_key][0]
        self.assertEqual(event1_data['title'], "Intro to Python")
        self.assertEqual(event1_data['venue'], "Room 101")
        self.assertEqual(event1_data['time'], "2:30 PM")

        event2_data = parsed_events[date_key][1]
        self.assertEqual(event2_data['title'], "Python Advanced")
        self.assertEqual(event2_data['venue'], "Lab 3")
        self.assertEqual(event2_data['time'], "4:00 PM")

        # The other event's date should not be present
        self.assertNotIn("2026-09-25", parsed_events)


class NotificationSystemTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.student_user = CustomUser.objects.create_user(
            email="notif_student@campus.edu",
            password="password123",
            role="STUDENT"
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            first_name="Alice",
            last_name="Wonder"
        )

        from apps.students.models import Notification
        self.notif1 = Notification.objects.create(
            student=self.student_profile,
            message="Your RSVP for Workshop 1 is confirmed!",
            is_read=False
        )
        self.notif2 = Notification.objects.create(
            student=self.student_profile,
            message="New announcement from Tech Club",
            is_read=False
        )

    def test_context_processor_unread_count(self):
        from apps.students.context_processors import unread_notifications_count
        from django.test import RequestFactory

        rf = RequestFactory()
        request = rf.get('/')
        request.user = self.student_user

        data = unread_notifications_count(request)
        self.assertEqual(data['unread_notifications'], 2)

    def test_notifications_view_marks_as_read(self):
        self.client.login(email="notif_student@campus.edu", password="password123")
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)

        # Check that notifications were passed
        notifications = response.context['notifications']
        self.assertEqual(len(notifications), 2)

        # Check database: both should now be marked as read
        self.notif1.refresh_from_db()
        self.notif2.refresh_from_db()
        self.assertTrue(self.notif1.is_read)
        self.assertTrue(self.notif2.is_read)

    def test_members_only_post_notifies_approved_members(self):
        from apps.clubs.models import ClubProfile, ClubMembership
        from apps.students.models import Notification

        club_user = CustomUser.objects.create_user(
            email="robotics@campus.edu",
            password="password123",
            role="CLUB"
        )
        club_profile = ClubProfile.objects.create(
            user=club_user,
            club_name="Robotics Club",
            category="Technical"
        )

        # Alice is approved member
        ClubMembership.objects.create(
            club=club_profile,
            student=self.student_profile,
            status="approved"
        )

        # Login as club user and publish a private post
        self.client.login(email="robotics@campus.edu", password="password123")
        response = self.client.post(reverse("create_post"), {
            "content": "Secret workshop schedule released!",
            "is_private": "true"
        })
        self.assertEqual(response.status_code, 302)

        # Alice should have received a notification
        notif = Notification.objects.filter(
            student=self.student_profile,
            message__startswith="New members-only update from Robotics Club:"
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("Secret workshop schedule released!", notif.message)
        self.assertFalse(notif.is_read)

    def test_members_only_event_notifies_approved_members(self):
        from apps.clubs.models import ClubProfile, ClubMembership
        from apps.students.models import Notification

        club_user = CustomUser.objects.create_user(
            email="ai_club@campus.edu",
            password="password123",
            role="CLUB"
        )
        club_profile = ClubProfile.objects.create(
            user=club_user,
            club_name="AI Club",
            category="Technical"
        )

        # Alice is approved member
        ClubMembership.objects.create(
            club=club_profile,
            student=self.student_profile,
            status="approved"
        )

        # Login as club user and publish a private event
        self.client.login(email="ai_club@campus.edu", password="password123")
        response = self.client.post(reverse("create_event"), {
            "title": "Exclusive AI Hackathon",
            "description": "Members only hackathon.",
            "category": "Technical",
            "venue": "Lab 404",
            "date": "2026-10-15",
            "time": "10:00",
            "is_private": "true",
            "rsvp_mode": "DIRECT"
        })
        self.assertEqual(response.status_code, 302)

        # Alice should have received a notification
        notif = Notification.objects.filter(
            student=self.student_profile,
            message="New members-only update from AI Club: Exclusive AI Hackathon"
        ).first()
        self.assertIsNotNone(notif)
        self.assertFalse(notif.is_read)


class StudentFeedChronologicalTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Club 1
        self.club_user1 = CustomUser.objects.create_user(
            email="club1@campus.edu",
            password="password123",
            role="CLUB"
        )
        self.club_profile1 = ClubProfile.objects.create(
            user=self.club_user1,
            club_name="Coding Society",
            category="Technical"
        )

        # Create Club 2
        self.club_user2 = CustomUser.objects.create_user(
            email="club2@campus.edu",
            password="password123",
            role="CLUB"
        )
        self.club_profile2 = ClubProfile.objects.create(
            user=self.club_user2,
            club_name="Secret Society",
            category="Special"
        )

        # Create Student User & Profile
        self.student_user = CustomUser.objects.create_user(
            email="feed_student@campus.edu",
            password="password123",
            role="STUDENT"
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            first_name="Sam",
            last_name="Fisher"
        )

        # Student is an approved member of Club 1 only
        from apps.clubs.models import ClubMembership, ClubPost
        ClubMembership.objects.create(
            club=self.club_profile1,
            student=self.student_profile,
            status="approved"
        )

        from django.utils import timezone
        now = timezone.now()

        # Item 1: Post 1 (oldest)
        self.post1 = ClubPost.objects.create(
            club=self.club_profile1,
            content="Oldest announcement",
            is_private=False
        )
        ClubPost.objects.filter(id=self.post1.id).update(created_at=now - datetime.timedelta(hours=4))
        self.post1.refresh_from_db()

        # Item 2: Event 1
        self.event1 = Event.objects.create(
            club=self.club_profile1,
            title="Intro Workshop",
            description="First event",
            date=datetime.date(2026, 10, 1),
            time=datetime.time(10, 0),
            venue="Hall 1",
            category="Technical",
            is_private=False
        )
        Event.objects.filter(id=self.event1.id).update(created_at=now - datetime.timedelta(hours=3))
        self.event1.refresh_from_db()

        # Item 3: Post 2
        self.post2 = ClubPost.objects.create(
            club=self.club_profile1,
            content="Mid-day announcement",
            is_private=False
        )
        ClubPost.objects.filter(id=self.post2.id).update(created_at=now - datetime.timedelta(hours=2))
        self.post2.refresh_from_db()

        # Item 4: Event 2 (newest)
        self.event2 = Event.objects.create(
            club=self.club_profile1,
            title="Advanced Hackathon",
            description="Second event",
            date=datetime.date(2026, 10, 2),
            time=datetime.time(14, 0),
            venue="Lab 2",
            category="Technical",
            is_private=False
        )
        Event.objects.filter(id=self.event2.id).update(created_at=now - datetime.timedelta(hours=1))
        self.event2.refresh_from_db()

        # Private item from Club 2 (Student is NOT a member)
        self.private_post_unauth = ClubPost.objects.create(
            club=self.club_profile2,
            content="Secret Society Post",
            is_private=True
        )
        ClubPost.objects.filter(id=self.private_post_unauth.id).update(created_at=now)
        self.private_post_unauth.refresh_from_db()

        # Private item from Club 1 (Student IS an approved member)
        self.private_post_auth = ClubPost.objects.create(
            club=self.club_profile1,
            content="Coding Society Members-Only Post",
            is_private=True
        )
        ClubPost.objects.filter(id=self.private_post_auth.id).update(created_at=now + datetime.timedelta(minutes=5))
        self.private_post_auth.refresh_from_db()

    def test_student_dashboard_timeline_chronological_ordering(self):
        self.client.login(email="feed_student@campus.edu", password="password123")
        response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(response.status_code, 200)

        timeline = list(response.context["timeline"])
        # Newest item must be index 0
        self.assertEqual(timeline[0], self.private_post_auth)
        self.assertEqual(timeline[1], self.event2)
        self.assertEqual(timeline[2], self.post2)
        self.assertEqual(timeline[3], self.event1)
        self.assertEqual(timeline[4], self.post1)

        # Unapproved private post must NOT be in timeline
        self.assertNotIn(self.private_post_unauth, timeline)

    def test_fetch_new_feed_items_endpoint(self):
        self.client.login(email="feed_student@campus.edu", password="password123")
        cutoff = self.post2.created_at.isoformat()

        response = self.client.get(reverse("fetch_new_feed_items"), {"latest_timestamp": cutoff})
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        # event2 and private_post_auth were created after post2
        self.assertIn("Advanced Hackathon", content)
        self.assertIn("Coding Society Members-Only Post", content)
        # Older items should not be present
        self.assertNotIn("Mid-day announcement", content)
        self.assertNotIn("Intro Workshop", content)
        self.assertNotIn("Oldest announcement", content)
        # Unapproved private post should never appear
        self.assertNotIn("Secret Society Post", content)

    def test_fetch_new_feed_items_no_newer_items(self):
        self.client.login(email="feed_student@campus.edu", password="password123")
        future_cutoff = (self.private_post_auth.created_at + datetime.timedelta(hours=1)).isoformat()

        response = self.client.get(reverse("fetch_new_feed_items"), {"latest_timestamp": future_cutoff})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8").strip(), "")



