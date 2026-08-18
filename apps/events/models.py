from django.db import models
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
    rsvp_mode = models.CharField(max_length=20, choices=RSVP_CHOICES, default='DIRECT')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.club.club_name}"


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