from django.http import JsonResponse
from django.urls import path


def root(_request):
    return JsonResponse({"message": "Hello from Django on Cloudflare Workers!"})


urlpatterns = [
    path("", root),
]
