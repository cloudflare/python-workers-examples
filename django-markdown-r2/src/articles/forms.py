from django import forms

from .models import Article


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ["title", "body", "image"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 16}),
            "image": forms.ClearableFileInput(
                attrs={"accept": "image/gif,image/jpeg,image/png,image/webp"}
            ),
        }
        help_texts = {"image": "PNG, JPEG, GIF, or WebP."}


class ArticleEditForm(ArticleForm):
    class Meta(ArticleForm.Meta):
        fields = ["title", "body"]
