from django.shortcuts import render
from apps.core.decorators import admin_required


@admin_required
def admin_dashboard(request):
    return render(request, "administration/dashboard.html")
