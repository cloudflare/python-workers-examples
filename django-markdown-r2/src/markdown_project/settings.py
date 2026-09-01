SECRET_KEY = "django-insecure-development-placeholder"
DEBUG = False
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "markdown_project.urls"
WSGI_APPLICATION = "markdown_project.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
INSTALLED_APPS = ["articles"]
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]
DATABASES = {
    "default": {
        "ENGINE": "markdown_project.db.backends.do",
    }
}
STORAGES = {
    "default": {
        "BACKEND": "django_cf.storage.R2Storage",
        "OPTIONS": {
            "binding": "IMAGES",
            "location": "images",
            "allow_overwrite": False,
        },
    }
}
MEDIA_URL = "/media/"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    }
]
TIME_ZONE = "UTC"
USE_TZ = False
