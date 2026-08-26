"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.http import JsonResponse
from django.urls import path, include


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


# @user_passes_test(is_superuser)
def create_admin_view(request):
    User = get_user_model()
    username = "admin"  # Or get from request, config, etc.
    email = "admin@example.com"  # Or get from request, config, etc.
    # IMPORTANT: Change this password or manage it securely!
    password = "password"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        return JsonResponse(
            {"status": "success", "message": f"Admin user '{username}' created."}
        )
    else:
        return JsonResponse(
            {"status": "info", "message": f"Admin user '{username}' already exists."}
        )


# @user_passes_test(is_superuser)
def run_migrations_view(request):
    try:
        call_command("migrate")
        return JsonResponse({"status": "success", "message": "Migrations applied."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": e.__str__()}, status=500)


urlpatterns = [
    path("", include("blog.urls")),
    path("admin/", admin.site.urls),
    # Management endpoints - secure these appropriately for your application
    path("__create_admin__/", create_admin_view, name="create_admin"),
    path("__run_migrations__/", run_migrations_view, name="run_migrations"),
]
