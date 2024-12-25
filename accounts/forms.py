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

    status = forms.ChoiceField(choices=(("Менеджер", "Менеджер"),("Администратор", "Администратор"),("Директор КЦ", "Директор КЦ"), ("Оператор", "Оператор"), ("Директор ЮПП", "Директор ЮПП"), ("Юрист пирвичник", "Юрист пирвичник"), ("Директор представителей", "Директор представителей"), ("Представитель", "Представитель")))

    password1 = forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"})

    password2 = forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"})

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "status",
            "password1",
            "password2",
        )
