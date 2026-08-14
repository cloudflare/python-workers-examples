from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "blog"
urlpatterns = [
    path("", TemplateView.as_view(template_name="landing.html"), name="landing"),
    path("blog/", views.post_list, name="post_list"),
    path("blog/post/<int:pk>/", views.post_detail, name="post_detail"),
]
