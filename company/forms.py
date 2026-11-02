from django import forms

from .models import Companys


class RegCompany(forms.ModelForm):
    class Meta:
        model = Companys
        fields = ["title", "work_mode"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-company"}),
            "work_mode": forms.RadioSelect(attrs={"class": "company-mode"}),
        }
        labels = {
            "title": "Название",
            "work_mode": "Как вы будете работать?",
        }
