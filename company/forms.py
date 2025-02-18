from django import forms
from .models import Companys


class RegCompany(forms.ModelForm):

    class Meta:
        model = Companys
        fields = "__all__"
        labels = {'title': 'Название', "telegram_bot":"id телеграм бота"}