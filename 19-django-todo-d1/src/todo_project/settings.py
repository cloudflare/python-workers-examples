SECRET_KEY = "django-insecure-development-placeholder"
DEBUG = False
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "todo_project.urls"
WSGI_APPLICATION = "todo_project.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
INSTALLED_APPS = [
    "todos",
]
MIDDLEWARE = []
DATABASES = {
    "default": {
        "ENGINE": "django_cf.db.backends.d1",
        "CLOUDFLARE_BINDING": "DB",
    }
}
TIME_ZONE = "UTC"
