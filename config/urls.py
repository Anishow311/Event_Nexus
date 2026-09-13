"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path("", include("apps.authentication.urls")),

    # Dedicated Domains
    path("student/", include("apps.students.urls")),
    path("club/", include("apps.clubs.urls")),
    path("events/", include("apps.events.urls")),
    path("event/", include("apps.events.urls")),
    path("admin-portal/", include("apps.administration.urls")),

    # Backward Compatibility Aliases for /dashboard/*
    path("dashboard/student/", include("apps.students.urls")),
    path("dashboard/club/", include("apps.clubs.urls")),
    path("dashboard/admin/", include("apps.administration.urls")),
]
