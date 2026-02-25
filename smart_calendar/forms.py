from django import forms

from accounts.models import User
from leads.models import Record

from .models import Booking


class AddEventForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Record.objects.none(),
        label="Клиент:",
    )

    time = forms.ChoiceField(
        choices=(),
        label="Время приема:",
    )

    employees = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Сотрудник:",
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        available_times = kwargs.pop("available_times")
        self.selected_date = kwargs.pop("selected_date")
        super().__init__(*args, **kwargs)

        self.fields["employees"].queryset = User.objects.filter(
            companys_id=self.user.companys_id,
            status="Р®СЂРёСЃС‚ РїРёСЂРІРёС‡РЅРёРє",
        )
        clients_queryset = Record.objects.filter(
            companys_id=self.user.companys_id,
            status="Р—Р°РїРёСЃСЊ РІ РѕС„РёСЃ",
        )
        if self.user.felial_id:
            clients_queryset = clients_queryset.filter(felial_id=self.user.felial_id)
        self.fields["client"].queryset = clients_queryset
        self.fields["time"].choices = [(t, t) for t in available_times if t != "none"]

    class Meta:
        model = Booking
        fields = ["client", "employees", "time"]
