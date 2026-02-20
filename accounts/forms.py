from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from felial.models import Felial

User = get_user_model()


class AddEmployeesForm(UserCreationForm):
    email = forms.EmailField(
        label="",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Email"}),
    )

    username = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя"}),
    )

    status = forms.ChoiceField(
        label="Статус сотрудника",
        choices=(
            ("Менеджер", "Менеджер"),
            ("Администратор", "Администратор"),
            ("Директор КЦ", "Директор КЦ"),
            ("Оператор", "Оператор"),
            ("Директор ЮПП", "Директор ЮПП"),
            ("Юрист пирвичник", "Юрист пирвичник"),
            ("Директор представителей", "Директор представителей"),
            ("Представитель", "Представитель"),
        ),
        widget=forms.Select(attrs={"class": "form-control", "style": "margin-bottom: 12px;"}),
    )

    type_zp = forms.ChoiceField(
        label="Тип ЗП",
        choices=(
            ("Процент", "Процент"),
            ("Ставка", "Ставка"),
            ("Процент + Ставка", "Процент + Ставка"),
        ),
        widget=forms.Select(attrs={"class": "form-control", "style": "margin-bottom: 12px;"}),
    )

    felial = forms.ModelChoiceField(
        label="Филиал",
        queryset=Felial.objects.all(),
        widget=forms.Select(attrs={"class": "form-select", "style": "width: 181px;"}),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["password1"].help_text = None
        self.fields["password2"].help_text = None

        if self.user:
            self.fields["felial"].queryset = Felial.objects.filter(companys=self.user.companys)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "status",
            "felial",
            "type_zp",
            "percent",
            "bet",
            "password1",
            "password2",
        )
        labels = {
            "type_zp": "Тип ЗП",
            "percent": "%",
            "bet": "Ставка",
        }


class AddSuperEmployeesForm(UserCreationForm):
    email = forms.EmailField(
        label="",
        widget=forms.TextInput(attrs={"class": "form-company", "placeholder": "Email"}),
    )
    username = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-company", "placeholder": "Имя"}),
    )

    password1 = forms.CharField(
        label="",
        widget=forms.PasswordInput(attrs={"class": "form-company", "placeholder": "Пароль"}),
    )

    password2 = forms.CharField(
        label="",
        widget=forms.PasswordInput(attrs={"class": "form-company", "placeholder": "Подтвердите пароль"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class EmployeeUpdateForm(forms.ModelForm):
    password = forms.CharField(
        label="Новый пароль",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "status",
            "felial",
            "type_zp",
            "percent",
            "bet",
            "password",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")

        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user
