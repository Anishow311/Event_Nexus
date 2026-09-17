from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        return self.create_user(
            email,
            password,
            **extra_fields
        )
class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    username = None
    email = models.EmailField(unique=True)
    objects = CustomUserManager()
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('CLUB', 'Club'),
        ('ADMIN', 'Admin'),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='STUDENT'
    )

    @property
    def clubprofile(self):
        return getattr(self, 'club_profile', None)

class StudentProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True, default="Student actively exploring clubs and events on campus.")
    major = models.CharField(max_length=100, blank=True, null=True)
    class_of = models.CharField(max_length=20, blank=True, null=True)
    interests = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_interests_list(self):
        if self.interests:
            return [i.strip() for i in self.interests.split(",") if i.strip()]
        return []


class ClubProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="club_profile"
    )
    club_name = models.CharField(max_length=200)
    
    # --- NEW FIELDS FOR THE PROFILE ---
    bio = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True, default="General")
    contact_email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='clubs/logos/', null=True, blank=True)
    followers = models.ManyToManyField(
        CustomUser,
        related_name="followed_clubs",
        blank=True
    )
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.club_name

    