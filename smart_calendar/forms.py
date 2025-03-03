from django import forms
from .models import Booking
from django.forms import ModelChoiceField

class AddEventForm(forms.ModelForm):

    class Meta:
        model = Booking
        fields = ['client', 'start_time', 'end_time']
        widgets = {
            "name": forms.DateTimeInput(attrs={"id": "start-time", "label": "Your name"})

        }
        labels = {'client': 'Клиент', "start_time":"Начло приема", "end_time":"Конец приема"}
