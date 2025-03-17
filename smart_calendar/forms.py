from django import forms
from .models import Booking
from accounts.models import User
from django.forms import ModelChoiceField

class AddEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Достаем пользователя из аргументов
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['employees'].queryset = User.objects.filter(companys=self.user.companys.id, status="Юрист пирвичник")

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

