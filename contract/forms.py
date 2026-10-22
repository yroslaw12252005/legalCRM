from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from cost.forms import Surcharge_form
from cost.models import Surcharge
from .models import Contract


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ["number", "amount", "initial_payment", "contract_date"]
        widgets = {
            "number": forms.TextInput(attrs={"class": "input", "inputmode": "numeric", "pattern": "[0-9]+"}),
            "amount": forms.NumberInput(attrs={"class": "input", "min": "0", "step": "0.01"}),
            "initial_payment": forms.NumberInput(attrs={"class": "input", "min": "0", "step": "0.01"}),
            "contract_date": forms.DateInput(attrs={"class": "input", "type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        number = cleaned_data.get("number")
        amount = cleaned_data.get("amount")
        initial_payment = cleaned_data.get("initial_payment")

        if number and self.instance.record_id:
            same_number = Contract.objects.filter(
                record_id=self.instance.record_id,
                number=number,
            )
            if self.instance.pk:
                same_number = same_number.exclude(pk=self.instance.pk)
            if same_number.exists():
                self.add_error("number", "У этого клиента уже есть договор с таким номером")

        if amount is not None and initial_payment is not None and initial_payment > amount:
            self.add_error(
                "initial_payment",
                "Сумма при заключении не может превышать сумму договора",
            )
        return cleaned_data


class BaseContractSurchargeFormSet(BaseInlineFormSet):
    def __init__(self, *args, expected_total=None, allow_existing_deletes=False, **kwargs):
        self.expected_total = expected_total
        self.allow_existing_deletes = allow_existing_deletes
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if any(self.errors) or self.expected_total is None:
            return

        surcharge_total = 0
        for form in self.forms:
            cleaned_data = getattr(form, "cleaned_data", None) or {}
            if cleaned_data.get("DELETE"):
                if form.instance.pk and not self.allow_existing_deletes:
                    raise ValidationError("Удалять существующие доплаты может только администратор")
                continue
            surcharge_total += cleaned_data.get("cost") or 0

        if surcharge_total != self.expected_total:
            raise ValidationError(
                "Сумма доплат должна быть равна остатку по договору: "
                f"{self.expected_total:.2f} руб. Сейчас указано: {surcharge_total:.2f} руб."
            )


ContractSurchargeFormSet = inlineformset_factory(
    Contract,
    Surcharge,
    form=Surcharge_form,
    formset=BaseContractSurchargeFormSet,
    extra=1,
    can_delete=True,
)

