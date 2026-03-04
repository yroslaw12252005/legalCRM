from django import forms

from .models import Companys


class RegCompany(forms.ModelForm):
    class Meta:
        model = Companys
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-company"}),
        }
        labels = {"title": "Название"}
