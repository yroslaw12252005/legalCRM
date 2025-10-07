from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User
from .models import Record
from felial.models import Felial
from django.forms import ModelChoiceField


class AddRecordForm(forms.ModelForm):
    status = forms.ChoiceField(widget=forms.Select(attrs={
            'class': 'form-select' # Опционально: inline-стили
        }), label="Статус заявки", choices=(
    ("Новая", "Новая"), ("Брак", "Брак"), ("Недозвон", "Недозвон"), ("Перезвон", "Перезвон"), ("Запись в офис", "Запись в офис"),
    ("Отказ", "Отказ"), ("Онлайн", "Онлайн"), ("Акт", "Акт"), ("Договор", "Договор")))
    
    type = forms.ChoiceField(widget=forms.Select(attrs={
                'class': 'form-select' # Опционально: inline-стили
            }), label="Тематика", choices=(
        ("Военка", "Военка"), ("Семейная", "Семейная"), ("Военная", "Военная"), ("Арбитраж", "Арбитраж")))


    where = forms.ChoiceField(widget=forms.Select(attrs={
            'class': 'form-select' # Опционально: inline-стили
        }), label="Источник", choices=(
        ("VK", "VK"), ("Tilda", "Tilda"), ("РЕ", "РЕ"), ("Звонок", "Звонок")))

    def __init__(self, *args, **kwargs):
        # Достаем пользователя из аргументов
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['felial'].queryset = Felial.objects.filter(companys=self.user.companys.id)

    felial = forms.ModelChoiceField(widget=forms.Select(attrs={
            'class': 'form-select', 'style':'width: 181px;' # Опционально: inline-стили
        }), queryset=Felial.objects.none(),
        initial = 0, label='Филиал')


    class Meta:
        model = Record
        fields = ['name', 'description', 'phone', 'status', 'type', 'where', 'felial']
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "label": "Your name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "cols":"40", "rows":"5"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),

        }
        labels = {'name': 'Имя', "description":"Описание", "phone":"Телефон", "status":"Статус", 'topic':'Тип заявки' ,"employees_KC":"Оператор", "employees_UPP":"Юрист",  'where':'Источник', 'felial':'Филиал'}

class StatusForm(forms.ModelForm):
    status = forms.ChoiceField(label="Статус заявки", choices=(
    ("Новая", "Новая"), ("Брак", "Брак"), ("Недозвон", "Недозвон"), ("Перезвон", "Перезвон"), ("Запись в офис", "Запись в офис"),
    ("Отказ", "Отказ"), ("Онлайн", "Онлайн"), ("Акт", "Акт"),("Договор", "Договор")))

    class Meta:
        model = Record
        fields = ['status']
        labels = {'status': 'Статус заявки'}

        
class TopicForm(forms.ModelForm):
    topic = forms.ChoiceField(widget=forms.Select(attrs={
                'class': 'form-select' # Опционально: inline-стили
            }), label="Тематика", choices=(
        ("Военка", "Военка"), ("Семейная", "Семейная"), ("Военная", "Военная"), ("Арбитраж", "Арбитраж")))

    class Meta:
        model = Record
        fields = ['topic']
        labels = {'topic': 'Тип заявки'}


class Employees_KCForm(forms.ModelForm):
    employees_KC = forms.ModelChoiceField(queryset=User.objects.filter(status="Оператор"), widget=forms.Select(attrs={
            'class': 'form-select',  # Добавляем класс для стилизации
            'style': 'margin-bottom: 12px;'  # Опционально: inline-стили
        }), label="")

    class Meta:
        model = User
        fields = ['employees_KC']
        labels = {'status': 'Оператор'}

class Employees_UPPForm(forms.ModelForm):
    employees_UPP = forms.ModelChoiceField(queryset=User.objects.filter(status="Юрист пирвичник"), widget=forms.Select(attrs={
            'class': 'form-select',  # Добавляем класс для стилизации
            'style': 'margin-bottom: 12px;'  # Опционально: inline-стили
        }), label="")

    class Meta:
        model = User
        fields = ['employees_UPP']
        labels = {'status': ''}


class CostForm(forms.ModelForm):
    cost = forms.DecimalField(label="Стоимость", widget=forms.TextInput(attrs={
            'class': 'form',  # Добавляем класс для стилизации
            'style': 'margin-bottom: 12px;'  # Опционально: inline-стили
        }) )

    class Meta:
        model = Record
        fields = ['cost']
        labels = {'cost': 'Стоимость'}


from django.core.validators import FileExtensionValidator

class FileUploadForm(forms.Form):
    file = forms.FileField(
        label='',
        widget=forms.FileInput(attrs={'class': 'file'}),
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])
        ]
    )