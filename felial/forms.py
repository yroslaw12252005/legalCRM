from felial.models import Felial
from django import forms
class AddFelialForm(forms.ModelForm):

    class Meta:
        model = Felial
        fields = ['title', 'cites']
