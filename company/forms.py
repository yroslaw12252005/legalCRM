from django import forms
from .models import Companys


class RegCompany(forms.ModelForm):

    class Meta:
        model = Companys
        fields = "__all__"
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-company"}),
            "telegram_bot": forms.TextInput(attrs={"class": "form-company"}),
        }
        labels = {'title': 'Название', "telegram_bot":"id телеграм бота"}