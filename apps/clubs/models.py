from django.db import models
from django.conf import settings


try:
    
    from cloudinary.models import CloudinaryField # pyrefly: ignore [missing-import]
except ImportError:
    CloudinaryField = models.ImageField

from apps.authentication.models import ClubProfile, StudentProfile


class ClubPost(models.Model):
    club = models.ForeignKey(
        ClubProfile,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    content = models.TextField()
    image = CloudinaryField('image', blank=True, null=True)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_posts",
        blank=True
    )
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.club.club_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class ClubMembership(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="club_memberships"
    )
    club = models.ForeignKey(
        ClubProfile,
        on_delete=models.CASCADE,
        related_name="memberships"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('student', 'club')

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.club.club_name} ({self.status})"

