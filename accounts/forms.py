from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import User

class AddEmployeesForm(UserCreationForm):
    email = forms.EmailField(
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Email"}
        ),
    )
    username = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Имя"}
        ),
    )

    status = forms.ChoiceField(widget=forms.Select(attrs={
            'class': 'form-control',  # Добавляем класс для стилизации
            'style': 'margin-bottom: 12px;'  # Опционально: inline-стили
        }),
        label="Статус сотрудника", choices=(("Менеджер", "Менеджер"),("Администратор", "Администратор"),("Директор КЦ", "Директор КЦ"), ("Оператор", "Оператор"), ("Директор ЮПП", "Директор ЮПП"), ("Юрист пирвичник", "Юрист пирвичник"), ("Директор представителей", "Директор представителей"), ("Представитель", "Представитель")))

    type_zp = forms.ChoiceField(widget=forms.Select(attrs={
            'class': 'form-control',  # Добавляем класс для стилизации
            'style': 'margin-bottom: 12px;'  # Опционально: inline-стили
        }), label="Тип ЗП", choices=(("Процент", "Процент"),("Оклад", "Оклад"),("Процент + Ставка", "Процент + Ставка")))

    password1 = forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"})

    password2 = forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "status",
            "type_zp",
            "percent",
            "bet",
            "password1",
            "password2",
        )
        labels = {'type_zp': 'Тип ЗП', 'percent':"%", "bet":"Ставка"}


class AddSuperEmployeesForm(UserCreationForm):
    email = forms.EmailField(
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-company", "placeholder": "Email"}
        ),
    )
    username = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-company", "placeholder": "Имя"}
        ),
    )

    password1 = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={"class": "form-company", "placeholder": "Пароль"}
        ),
    )

    password2 = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={"class": "form-company", "placeholder": "Подтвердите пароль"}
        ),
    )


class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )