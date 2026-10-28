from django import forms

from company.models import Companys


class PaymentValidationForm(forms.Form):
    company = forms.ModelChoiceField(
        label="Компания",
        queryset=Companys.objects.none(),
        empty_label="Выберите компанию",
    )
    amount = forms.DecimalField(
        label="Сумма пополнения",
        min_value=0.01,
        max_digits=14,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01", "placeholder": "Например, 10 000"}),
    )
    comment = forms.CharField(
        label="Комментарий",
        required=False,
        max_length=255,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Необязательно"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = Companys.objects.order_by("title")
