from django.core.exceptions import ValidationError

from django import forms

from .models import Article


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ["title", "slug", "body", "image"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 16}),
            "image": forms.ClearableFileInput(
                attrs={"accept": "image/gif,image/jpeg,image/png,image/webp"}
            ),
        }
        help_texts = {"image": "PNG, JPEG, GIF, or WebP."}

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        matches = Article.objects.filter(slug=slug)
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise ValidationError("An article with this slug already exists.")
        return slug


class ArticleEditForm(ArticleForm):
    class Meta(ArticleForm.Meta):
        fields = ["title", "slug", "body"]
