from django import forms
from .models import Surcharge
class Surcharge_form(forms.ModelForm):

    class Meta:
        model = Surcharge
        fields = ['cost']
        widgets = {
            'cost': forms.TextInput(attrs={'class': 'input'}),
            # and so on
        }
        labels = {'cost': 'Доплата'}
