from django import forms

from leads.models import Record
from .models import Booking
from accounts.models import User
from django.forms import ModelChoiceField

class AddEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Достаем пользователя из аргументов
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['employees'].queryset = User.objects.filter(companys=self.user.companys.id, status="Юрист пирвичник")

    client = forms.ModelChoiceField(queryset=Record.objects.filter(status="Запись в офис"), label="")
    employees = forms.ModelChoiceField(queryset=User.objects.none(),
        initial = 0, label='Сотруднк')

    class Meta:
        model = Booking
        fields = ['client', 'start_time', 'end_time', "employees"]
        widgets = {
            "start_time": forms.TextInput(attrs={"type": "datetime-local"}),
            "end_time": forms.TextInput(attrs={"type": "datetime-local"}),

        }
        labels = {'client': 'Клиент', "start_time":"Начло приема", "end_time":"Конец приема"}

class comeEventForm(forms.ModelForm):
    come = forms.ChoiceField(label="Дошел/Не дошел", choices=(
        (1,"Дошел"), (2,"Не дошел")))
    class Meta:
        model = Booking
        fields = ['come']
