from felial.models import Felial
from django import forms
class AddFelialForm(forms.ModelForm):
    class Meta:
        model = Felial
        fields = ['title', 'cites']
        labels = {'title': 'Название фелиала', "cites": "Город"}
        widgets = {
            "title": forms.TextInput(attrs={'class': 'title_felial', 'placeholder': ""}),
            "cites": forms.TextInput(attrs={'class': 'title_felial', 'placeholder': ""}),
        }
