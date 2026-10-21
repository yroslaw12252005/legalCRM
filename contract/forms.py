from django import forms

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

