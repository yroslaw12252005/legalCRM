from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Record
from accounts.models import User
from felial.models import Felial
from django.forms import ModelChoiceField

class AddRecordForm(forms.ModelForm):
    status = forms.ChoiceField(label="Статус заявки", choices=(
    ("Новая", "Новая"), ("Брак", "Брак"), ("Недозвон", "Недозвон"), ("Перезвон", "Перезвон"), ("Запись в офис", "Запись в офис"),
    ("Отказ", "Отказ"), ("Онлайн", "Онлайн"), ("Акт", "Акт"), ("Договор", "Договор")))

    where = forms.ChoiceField(label="Источник", choices=(
        ("VK", "VK"), ("Tilda", "Tilda"), ("РЕ", "РЕ"), ("Звонок", "Звонок")))

    def __init__(self, *args, **kwargs):
        # Достаем пользователя из аргументов
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['felial'].queryset = Felial.objects.filter(companys=self.user.companys.id)

    felial = forms.ModelChoiceField(queryset=Felial.objects.none(),
        initial = 0, label='Фелиал')

    class Meta:
        model = Record
        fields = ['name', 'description', 'phone', 'status', 'where', 'felial']
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "label": "Your name"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {'name': 'Имя', "description":"Описание", "phone":"Телефон", "status":"Статус", "employees_KC":"Оператор", "employees_UPP":"Юрист",  'where':'Источник', 'felial':'Филиал'}

class StatusForm(forms.ModelForm):
    status = forms.ChoiceField(label="Статус заявки", choices=(
    ("Новая", "Новая"), ("Брак", "Брак"), ("Недозвон", "Недозвон"), ("Перезвон", "Перезвон"), ("Запись в офис", "Запись в офис"),
    ("Отказ", "Отказ"), ("Онлайн", "Онлайн"), ("Акт", "Акт"),("Договор", "Договор")))

    class Meta:
        model = Record
        fields = ['status']
        labels = {'status': 'Статус заявки'}

class Employees_KCForm(forms.ModelForm):
    employees_KC = forms.ModelChoiceField(queryset=User.objects.filter(status="Оператор"), label="")

    class Meta:
        model = User
        fields = ['employees_KC']
        labels = {'status': 'Оператор'}

class Employees_UPPForm(forms.ModelForm):
    employees_UPP = forms.ModelChoiceField(queryset=User.objects.filter(status="Юрист пирвичник"), label="")

    class Meta:
        model = User
        fields = ['employees_UPP']
        labels = {'status': ''}


class CostForm(forms.ModelForm):
    cost = forms.DecimalField(label="Стоимость" )

    class Meta:
        model = Record
        fields = ['cost']
        labels = {'cost': 'Стоимость'}