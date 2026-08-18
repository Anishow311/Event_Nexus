from django.contrib import admin
from .models import Event

# This tells Django to show our Event table in the Admin Panel
admin.site.register(Event)
