from datetime import datetime

from django import forms

from .models import Surcharge


class Surcharge_form(forms.ModelForm):
    date = forms.DateField(
        label="Дата доплаты",
        widget=forms.DateInput(attrs={"class": "input", "type": "date"}),
    )
    time = forms.ChoiceField(
        choices=(),
        label="Время доплаты",
        widget=forms.Select(attrs={"class": "input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        time_choices = [(f"{h:02}:{m:02}", f"{h:02}:{m:02}") for h in range(9, 19) for m in (0, 15, 30, 45)]
        self.fields["time"].choices = time_choices

    class Meta:
        model = Surcharge
        fields = ["cost"]
        widgets = {
            "cost": forms.TextInput(attrs={"class": "input"}),
        }
        labels = {
            "cost": "Сумма доплаты",
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        date_value = self.cleaned_data["date"]
        time_value = self.cleaned_data["time"]
        instance.dat = datetime.combine(date_value, datetime.strptime(time_value, "%H:%M").time())
        if commit:
            instance.save()
        return instance
