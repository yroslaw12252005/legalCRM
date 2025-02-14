from .models import Coming
from leads.models import Record
from django import forms

class AddComing(forms.ModelForm):
    date = forms.DateField(label="Записать на")
    lead = forms.ModelChoiceField(queryset=Record.objects.all(), label="Клиент")

    class Meta:
        model = Coming
        fields = "__all__"
        widgets = {
            'date':forms.TextInput(attrs={'class': 'input'}),
            "come": forms.HiddenInput(),
        }
        #labels = {'name': 'Имя', "description":"Описание", "phone":"Телефон", "status":"Статус", "employees_KC":"Оператор", "employees_UPP":"Юрист"}




