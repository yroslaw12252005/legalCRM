from django import forms
from .models import Surcharge
class Surcharge_form(forms.ModelForm):

    class Meta:
        model = Surcharge
        fields = "__all__"
        widgets = {
            'surcharge': forms.TextInput(attrs={'class': 'input'}),
            'record': forms.TextInput(attrs={'class': 'input'}),
            # and so on
        }
        labels = {'surcharge': 'Доплата', 'date': 'Дата доплаты', "record":"Клиен"}
