from django import forms
from .models import Surcharge
class Surcharge_form(forms.ModelForm):

    class Meta:
        model = Surcharge
        fields = ['cost', 'dat']
        widgets = {
            'cost': forms.TextInput(attrs={'class': 'input'}),
            'dat': forms.TextInput(attrs={'class': 'input', 'type':'datetime-local'}),
            # and so on
        }
        labels = {'cost': 'Доплата'}
