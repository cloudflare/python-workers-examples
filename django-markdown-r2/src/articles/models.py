import uuid

from django.core.validators import FileExtensionValidator
from django.db import models


def generate_article_id():
    return str(uuid.uuid4())


class Article(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=generate_article_id)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    body = models.TextField(max_length=20_000)
    image = models.FileField(
        upload_to="articles",
        blank=True,
        validators=[FileExtensionValidator(["gif", "jpeg", "jpg", "png", "webp"])],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "articles"
        ordering = ["-created_at"]
