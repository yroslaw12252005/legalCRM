from django import forms

from .models import Category, Material


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        labels = {"name": "Название категории"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["title", "body", "document", "category"]
        labels = {
            "title": "Заголовок",
            "body": "Основной текст",
            "document": "Документ",
            "category": "Категория",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 8}),
            "document": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }
