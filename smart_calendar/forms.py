from django import forms

from leads.models import Record
from .models import Booking
from accounts.models import User
from django.forms import ModelChoiceField
from datetime import datetime, time, timedelta
from datetime import date

class AddEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        available_times = kwargs.pop('available_times')
        self.selected_date = kwargs.pop('selected_date')
        super().__init__(*args, **kwargs)

        self.fields['employees'].queryset = User.objects.filter(companys=self.user.companys.id,
                                                                status="Юрист пирвичник")
        self.fields['time_slot'].choices = [(t, t) for t in available_times]

    client = forms.ModelChoiceField(
        queryset=Record.objects.filter(status="Запись в офис"),
        label="Клиент"
    )

    time_slot = forms.ChoiceField(
        choices=(),
        label="Время приема"
    )

    employees = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label='Сотрудник'
    )

    class Meta:
        model = Booking
        fields = ['client', 'employees', 'time_slot']

    def save(self, commit=True):
        instance = super().save(commit=False)
        time_obj = datetime.strptime(self.cleaned_data['time_slot'], "%H:%M").time()
        instance.start_time = datetime.combine(self.selected_date, time_obj)
        instance.end_time = instance.start_time + timedelta(minutes=15)
        if commit:
            instance.save()
        return instance


class comeEventForm(forms.ModelForm):
    come = forms.ChoiceField(label="Дошел/Не дошел", choices=(
        (1,"Дошел"), (2,"Не дошел")))
    class Meta:
        model = Booking
        fields = ['come']
