from django.contrib import admin
from .models import CustomUser, StudentProfile, ClubProfile

# This tells Django to show our user tables in the Admin Panel
admin.site.register(CustomUser)
admin.site.register(StudentProfile)
admin.site.register(ClubProfile)
