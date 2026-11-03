from django import forms

from felial.models import Felial

from .models import TildaIntegration


DEFAULT_MAPPING_TEXT = {
    "name": "name, fullname, fio, your_name, имя, фио",
    "phone": "phone, tel, telephone, mobile, custom_phone, телефон",
    "email": "email, mail, почта",
    "comment": "comment, comments, message, textarea, question, комментарий",
}


class TildaIntegrationForm(forms.ModelForm):
    name_fields = forms.CharField(label="Поля имени", required=True)
    phone_fields = forms.CharField(label="Поля телефона", required=True)
    email_fields = forms.CharField(label="Поля почты", required=False)
    comment_fields = forms.CharField(label="Поля комментария", required=False)
    allowed_form_ids_text = forms.CharField(
        required=False,
        label="Разрешённые formid",
        help_text="По одному ID формы в строке. Оставьте пустым, чтобы принимать все формы.",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "form48844953"}),
    )

    class Meta:
        model = TildaIntegration
        fields = [
            "title",
            "branch",
            "name_fields",
            "phone_fields",
            "email_fields",
            "comment_fields",
            "allowed_form_ids_text",
            "is_active",
        ]
        labels = {
            "title": "Название подключения",
            "branch": "Филиал для новых заявок",
            "is_active": "Подключение активно",
        }

    def __init__(self, *args, company, **kwargs):
        self.company = company
        super().__init__(*args, **kwargs)
        self.fields["branch"].queryset = Felial.objects.filter(companys=company).order_by("id")
        self.fields["branch"].required = False
        if self.instance and self.instance.pk:
            self.fields["allowed_form_ids_text"].initial = "\n".join(self.instance.allowed_form_ids or [])
        mapping = self.instance.field_mapping if self.instance and self.instance.pk else {}
        for kind in ("name", "phone", "email", "comment"):
            aliases = mapping.get(kind) if mapping else None
            self.fields[f"{kind}_fields"].initial = ", ".join(aliases or DEFAULT_MAPPING_TEXT[kind].split(", "))

    def clean_branch(self):
        branch = self.cleaned_data.get("branch")
        branches = Felial.objects.filter(companys=self.company)
        if branch and branch.companys_id != self.company.id:
            raise forms.ValidationError("Филиал должен принадлежать вашей компании.")
        if not branch:
            if branches.count() == 1:
                return branches.first()
            if branches.count() > 1:
                raise forms.ValidationError("Выберите филиал для заявок из этой формы.")
        return branch

    def clean_allowed_form_ids_text(self):
        value = self.cleaned_data.get("allowed_form_ids_text", "")
        form_ids = []
        for line in value.replace(",", "\n").splitlines():
            form_id = line.strip()
            if not form_id:
                continue
            if len(form_id) > 100:
                raise forms.ValidationError("ID формы не может быть длиннее 100 символов.")
            if form_id not in form_ids:
                form_ids.append(form_id)
        return form_ids

    def _clean_mapping_field(self, field_name):
        value = self.cleaned_data.get(field_name, "")
        aliases = []
        for item in value.replace("\n", ",").split(","):
            alias = item.strip()
            if not alias:
                continue
            if len(alias) > 100:
                raise forms.ValidationError("Название поля не может быть длиннее 100 символов.")
            if alias not in aliases:
                aliases.append(alias)
        return aliases

    def clean_name_fields(self):
        aliases = self._clean_mapping_field("name_fields")
        if not aliases:
            raise forms.ValidationError("Укажите хотя бы одно поле имени.")
        return aliases

    def clean_phone_fields(self):
        aliases = self._clean_mapping_field("phone_fields")
        if not aliases:
            raise forms.ValidationError("Укажите хотя бы одно поле телефона.")
        return aliases

    def clean_email_fields(self):
        return self._clean_mapping_field("email_fields")

    def clean_comment_fields(self):
        return self._clean_mapping_field("comment_fields")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.company = self.company
        instance.allowed_form_ids = self.cleaned_data["allowed_form_ids_text"]
        instance.field_mapping = {
            kind: self.cleaned_data[f"{kind}_fields"]
            for kind in ("name", "phone", "email", "comment")
        }
        if commit:
            instance.save()
        return instance
