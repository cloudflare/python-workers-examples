from articles import views
from django.urls import path

urlpatterns = [
    path("", views.article_list, name="article-list"),
    path("articles/new/", views.article_create, name="article-create"),
    path("articles/<slug:slug>/", views.article_detail, name="article-detail"),
    path("articles/<slug:slug>/edit/", views.article_edit, name="article-edit"),
    path("media/images/<path:name>", views.media_image, name="media-image"),
]
