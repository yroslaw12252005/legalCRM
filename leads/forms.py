from django import forms
from django.core.validators import FileExtensionValidator

from accounts.models import User
from felial.models import Felial

from .models import Record


def _tenant_user_queryset(user, status, company_id=None):
    queryset = User.objects.filter(status=status)
    tenant_id = company_id or getattr(user, "companys_id", None)
    if tenant_id:
        queryset = queryset.filter(companys_id=tenant_id)
    return queryset.order_by("username")


class AddRecordForm(forms.ModelForm):
    status = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Статус заявки",
        choices=(
            ("Новая", "Новая"),
            ("Брак", "Брак"),
            ("Недозвон", "Недозвон"),
            ("Перезвон", "Перезвон"),
            ("Запись в офис", "Запись в офис"),
            ("Отказ", "Отказ"),
            ("Онлайн", "Онлайн"),
            ("Акт", "Акт"),
            ("Договор", "Договор"),
        ),
    )

    type = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Тематика",
        choices=(("Военка", "Военка"), ("Семейная", "Семейная"), ("Военная", "Военная"), ("Арбитраж", "Арбитраж")),
    )

    where = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Источник",
        choices=(("VK", "VK"), ("Tilda", "Tilda"), ("РЕ", "РЕ"), ("Звонок", "Звонок")),
    )

    felial = forms.ModelChoiceField(
        widget=forms.Select(attrs={"class": "form-select", "style": "width: 181px;"}),
        queryset=Felial.objects.none(),
        initial=0,
        label="Филиал",
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.companys_id:
            self.fields["felial"].queryset = Felial.objects.filter(companys=self.user.companys_id)

    class Meta:
        model = Record
        fields = ["name", "description", "phone", "status", "type", "where", "felial"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "label": "Your name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "cols": "40", "rows": "5"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "name": "Имя",
            "description": "Описание",
            "phone": "Телефон",
            "status": "Статус",
            "type": "Тип заявки",
            "employees_KC": "Оператор",
            "employees_UPP": "Юрист",
            "employees_REP": "Представитель",
            "where": "Источник",
            "felial": "Филиал",
        }


class StatusForm(forms.ModelForm):
    status = forms.ChoiceField(
        label="Статус заявки",
        choices=(
            ("Новая", "Новая"),
            ("Брак", "Брак"),
            ("Недозвон", "Недозвон"),
            ("Перезвон", "Перезвон"),
            ("Запись в офис", "Запись в офис"),
            ("Отказ", "Отказ"),
            ("Онлайн", "Онлайн"),
            ("Акт", "Акт"),
            ("Договор", "Договор"),
        ),
    )

    class Meta:
        model = Record
        fields = ["status"]
        labels = {"status": "Статус заявки"}


class Employees_KCForm(forms.ModelForm):
    employees_KC = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "style": "margin-bottom: 12px;"}),
        label="",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        company_id = kwargs.pop("company_id", None) or getattr(kwargs.get("instance"), "companys_id", None)
        super().__init__(*args, **kwargs)
        self.fields["employees_KC"].queryset = _tenant_user_queryset(user, "Оператор", company_id=company_id)

    class Meta:
        model = Record
        fields = ["employees_KC"]


class Employees_UPPForm(forms.ModelForm):
    employees_UPP = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "style": "margin-bottom: 12px;"}),
        label="",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        company_id = kwargs.pop("company_id", None) or getattr(kwargs.get("instance"), "companys_id", None)
        super().__init__(*args, **kwargs)
        self.fields["employees_UPP"].queryset = _tenant_user_queryset(user, "Юрист пирвичник", company_id=company_id)

    class Meta:
        model = Record
        fields = ["employees_UPP"]


class Employees_REPForm(forms.ModelForm):
    employees_REP = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "style": "margin-bottom: 12px;"}),
        label="",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        company_id = kwargs.pop("company_id", None) or getattr(kwargs.get("instance"), "companys_id", None)
        super().__init__(*args, **kwargs)
        self.fields["employees_REP"].queryset = _tenant_user_queryset(user, "Представитель", company_id=company_id)

    class Meta:
        model = Record
        fields = ["employees_REP"]


class CostForm(forms.ModelForm):
    cost = forms.DecimalField(
        label="Стоимость",
        widget=forms.TextInput(attrs={"class": "form", "style": "margin-bottom: 12px;"}),
    )

    class Meta:
        model = Record
        fields = ["cost"]
        labels = {"cost": "Стоимость"}


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        extension_validator = FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])
        if isinstance(data, (list, tuple)):
            cleaned_files = [single_file_clean(file, initial) for file in data]
            for file in cleaned_files:
                extension_validator(file)
            return cleaned_files
        cleaned_file = single_file_clean(data, initial)
        extension_validator(cleaned_file)
        return [cleaned_file]


class FileUploadForm(forms.Form):
    file = MultipleFileField(label="", widget=MultipleFileInput(attrs={"class": "file"}))
