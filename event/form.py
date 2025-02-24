from django import forms
from .models import Event

class AddEventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = ['client', 'title', 'time', 'description', 'user']
        #labels = {'name': 'Имя', "description":"Описание", "phone":"Телефон", "status":"Статус", "employees_KC":"Оператор", "employees_UPP":"Юрист",  'where':'Источник', 'felial':'Фелиал'}
