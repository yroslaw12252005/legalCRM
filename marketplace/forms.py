from django import forms

from company.models import Companys

from .models import MIN_LEAD_PRICE, LeadStreamSettings


class LeadStreamSettingsForm(forms.ModelForm):
    class Meta:
        model = LeadStreamSettings
        fields = ("work_start", "work_end", "budget", "lead_price", "is_enabled")
        widgets = {
            "work_start": forms.TimeInput(attrs={"type": "time", "class": "flow-input"}, format="%H:%M"),
            "work_end": forms.TimeInput(attrs={"type": "time", "class": "flow-input"}, format="%H:%M"),
            "budget": forms.NumberInput(attrs={"class": "flow-input", "step": "0.01", "min": "0"}),
            "lead_price": forms.NumberInput(
                attrs={"class": "flow-input", "step": "0.01", "min": "300"}
            ),
            "is_enabled": forms.CheckboxInput(attrs={"class": "flow-checkbox"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("work_start")
        end = cleaned.get("work_end")
        if start and end and start >= end:
            self.add_error("work_end", "Время окончания должно быть позже времени начала")
        lead_price = cleaned.get("lead_price")
        if lead_price is not None and lead_price < MIN_LEAD_PRICE:
            self.add_error("lead_price", "Минимальная стоимость заявки — 300 ₽")
        if cleaned.get("is_enabled") and not cleaned.get("budget"):
            self.add_error("budget", "Для включения потока укажите бюджет")
        return cleaned


class LeadDistributionForm(forms.Form):
    company = forms.ModelChoiceField(
        label="Компания",
        queryset=Companys.objects.none(),
        empty_label="Выберите компанию",
        widget=forms.Select(attrs={"class": "distribution-select"}),
    )
    lead_ids = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = Companys.objects.filter(
            lead_stream_settings__is_enabled=True,
            lead_stream_settings__lead_price__gte=MIN_LEAD_PRICE,
        ).select_related("lead_stream_settings", "wallet").order_by("title")

    def clean_lead_ids(self):
        raw_value = self.cleaned_data["lead_ids"]
        try:
            ids = sorted({int(value) for value in raw_value.split(",") if value.strip()})
        except (TypeError, ValueError):
            raise forms.ValidationError("Некорректный список заявок")
        if not ids:
            raise forms.ValidationError("Выберите хотя бы одну заявку")
        return ids
