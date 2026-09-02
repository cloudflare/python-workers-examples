from datetime import datetime
from pathlib import PurePosixPath

from django.core.files.storage import default_storage
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.safestring import SafeString, mark_safe
from markdown_it import MarkdownIt

from .forms import ArticleEditForm, ArticleForm
from .models import Article

IMAGE_CONTENT_TYPES: dict[str, str] = {
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def render_markdown(markdown: str) -> SafeString:
    return mark_safe(MarkdownIt("js-default").render(markdown))


def format_date(value: datetime) -> str:
    return f"{value:%B} {value.day}, {value.year}"


def article_list(request):
    articles = list(Article.objects.all())
    for article in articles:
        article.rendered_body = render_markdown(article.body)
        article.updated_date = format_date(article.updated_at)
        article.updated_iso = article.updated_at.isoformat()
    return render(request, "articles/article_list.html", {"articles": articles})


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    return render(
        request,
        "articles/article_detail.html",
        {
            "article": article,
            "created_date": format_date(article.created_at),
            "created_iso": article.created_at.isoformat(),
            "rendered_body": render_markdown(article.body),
            "updated_date": format_date(article.updated_at),
            "updated_iso": article.updated_at.isoformat(),
        },
    )


def article_create(request):
    form = ArticleForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        article = form.save()
        return redirect("article-detail", slug=article.slug)
    return render(
        request, "articles/article_form.html", {"form": form, "is_edit": False}
    )


def article_edit(request, slug):
    article = get_object_or_404(Article, slug=slug)
    form = ArticleEditForm(request.POST or None, instance=article)
    if request.method == "POST" and form.is_valid():
        article = form.save()
        return redirect("article-detail", slug=article.slug)
    return render(
        request,
        "articles/article_form.html",
        {"article": article, "form": form, "is_edit": True},
    )


def media_image(_request, name: str) -> HttpResponse:
    path = PurePosixPath(name)
    content_type = IMAGE_CONTENT_TYPES.get(path.suffix.lower())
    if content_type is None or not default_storage.exists(name):
        raise Http404
    with default_storage.open(name, "rb") as image_file:
        response = HttpResponse(image_file.read(), content_type=content_type)
    response["Content-Disposition"] = "inline"
    response["X-Content-Type-Options"] = "nosniff"
    return response
