from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Record
from accounts.models import User


class AddRecordForm(forms.ModelForm):
    status = forms.ChoiceField(label="Статус заявки", choices=(
    ("Новая", "Новая"), ("Брак", "Брак"), ("Недозвон", "Недозвон"), ("Перезвон", "Перезвон"), ("Запись в офис", "Запись в офис"),
    ("Отказ", "Отказ"), ("Онлайн", "Онлайн"), ("Акт", "Акт")))

    class Meta:
        model = Record
        fields = "__all__"
        fields = ['name', 'description', 'phone', 'status']
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "label": "Your name"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {'name': 'Имя', "description":"Описание", "phone":"Телефон", "status":"Статус", "employees_KC":"Оператор", "employees_UPP":"Юрист"}

class StatusForm(forms.ModelForm):
    status = forms.ChoiceField(label="Статус заявки", choices=(
    ("Новая", "Новая"), ("Брак", "Брак"), ("Недозвон", "Недозвон"), ("Перезвон", "Перезвон"), ("Запись в офис", "Запись в офис"),
    ("Отказ", "Отказ"), ("Онлайн", "Онлайн"), ("Акт", "Акт")))

    class Meta:
        model = Record
        fields = ['status']
        labels = {'status': 'Статус заявки'}

class Employees_KCForm(forms.ModelForm):
    employees_KC = forms.ModelChoiceField(queryset=User.objects.filter(status="Оператор"), label="Оператор")
    class Meta:
        model = User
        fields = ['employees_KC']
        labels = {'status': 'Оператор'}

class Employees_UPPForm(forms.ModelForm):
    employees_UPP = forms.ModelChoiceField(queryset=User.objects.filter(status="Юрист пирвичник"), label="Юрист")
    class Meta:
        model = User
        fields = ['employees_UPP']
        labels = {'status': 'Юрист'}
