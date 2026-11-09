from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from felial.models import Felial

User = get_user_model()


class SalaryFieldsMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type_zp"].required = True
        self.fields["percent"].required = False
        self.fields["bet"].required = False

    def clean(self):
        cleaned_data = super().clean()
        salary_type = cleaned_data.get("type_zp")
        percent = cleaned_data.get("percent")
        salary = cleaned_data.get("bet")

        uses_percent = salary_type in {User.SALARY_PERCENT, User.SALARY_COMBINED}
        uses_salary = salary_type in {User.SALARY_FIXED, User.SALARY_COMBINED}
        if uses_percent and percent is None:
            self.add_error("percent", "Укажите процент сотрудника")
        if uses_salary and salary is None:
            self.add_error("bet", "Укажите месячный оклад сотрудника")
        if not uses_percent:
            cleaned_data["percent"] = None
        if not uses_salary:
            cleaned_data["bet"] = None
        return cleaned_data


class UniqueEmailMixin:
    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        users = User.objects.filter(email__iexact=email)
        if getattr(self.instance, "pk", None):
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email


class AddEmployeesForm(SalaryFieldsMixin, UniqueEmailMixin, UserCreationForm):
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
        choices=User.SALARY_TYPE_CHOICES,
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
            if self.user.status == "Директор ЮПП":
                self.fields["status"].choices = (
                    ("Юрист пирвичник", "Юрист пирвичник"),
                )
            elif self.user.status == "Директор КЦ":
                self.fields["status"].choices = (("Оператор", "Оператор"),)

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
            "percent": "Процент, %",
            "bet": "Месячный оклад",
        }
        widgets = {
            "percent": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "100", "step": "0.001"}),
            "bet": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
        }


class AddSuperEmployeesForm(UniqueEmailMixin, UserCreationForm):
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


class EmployeeUpdateForm(SalaryFieldsMixin, UniqueEmailMixin, forms.ModelForm):
    password = forms.CharField(
        label="Новый пароль",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["felial"].queryset = Felial.objects.filter(companys=user.companys)

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
        widgets = {
            "type_zp": forms.Select(attrs={"class": "form-control"}),
            "percent": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "100", "step": "0.001"}),
            "bet": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")

        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user


class SoloProfileUpdateForm(UniqueEmailMixin, forms.ModelForm):
    password = forms.CharField(
        label="Новый пароль",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
                "placeholder": "Оставьте пустым, чтобы не менять",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "autocomplete": "email"}
            ),
        }
        labels = {
            "username": "Имя",
            "email": "Email для входа",
        }

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
