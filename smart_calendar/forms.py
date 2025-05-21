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
        self.fields['time'].choices = [(t, t) for t in available_times if t != 'none']


    client = forms.ModelChoiceField(
        queryset=Record.objects.filter(status="Запись в офис"),
        label="Клиент"
    )

    time = forms.ChoiceField(
        choices=(),
        label="Время приема"
    )

    employees = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label='Сотрудник'
    )

    class Meta:
        model = Booking
        fields = ['client', 'employees', 'time']



