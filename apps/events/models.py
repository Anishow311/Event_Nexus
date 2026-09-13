from datetime import date
from django.db import models
from django.conf import settings
from apps.authentication.models import ClubProfile, StudentProfile

class Event(models.Model):
    RSVP_CHOICES = (
        ('DISABLED', 'Disabled'),
        ('DIRECT', 'Direct RSVP'),
        ('CUSTOM', 'Custom RSVP'),
    )

    club = models.ForeignKey(ClubProfile, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    venue = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    
    image = models.ImageField(upload_to='events/images/', null=True, blank=True)
    
    total_seats = models.PositiveIntegerField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    rsvp_mode = models.CharField(max_length=20, choices=RSVP_CHOICES, default='DIRECT')
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_events', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.club.club_name}"

    @property
    def is_past(self):
        """
        Compares event.date to today's date.
        Returns True if the event date is in the past, and False if it is today or in the future.
        """
        return self.date < date.today()

    @property
    def attendees(self):
        """
        Returns a queryset of CustomUsers who are registered for this event.
        Enables template conditions like `{% if request.user in event.attendees.all %}`.
        """
        from apps.authentication.models import CustomUser
        return CustomUser.objects.filter(student_profile__registrations__event=self)



# NEW: The digital sign-up sheet connecting a Student to an Event
class Registration(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Security: This prevents a student from RSVPing to the same event twice!
        unique_together = ('student', 'event')

    def __str__(self):
        return f"{self.student.first_name} registered for {self.event.title}"


class CustomQuestion(models.Model):
    QUESTION_TYPE_CHOICES = (
        ('SHORT_ANSWER', 'Short Answer'),
        ('PARAGRAPH', 'Paragraph'),
        ('MULTIPLE_CHOICE', 'Multiple Choice'),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='custom_questions')
    question_text = models.CharField(max_length=255)
    question_type = models.CharField(
        max_length=50,
        choices=QUESTION_TYPE_CHOICES,
        default='SHORT_ANSWER'
    )
    is_required = models.BooleanField(default=True)

    def __str__(self):
        return self.question_text


class QuestionOption(models.Model):
    question = models.ForeignKey(CustomQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=200)

    def __str__(self):
        return self.option_text


class StudentAnswer(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(CustomQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()

    def __str__(self):
        return f"{self.registration.student.first_name} - {self.question.question_text}"
