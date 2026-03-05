from django import forms

from accounts.models import User
from leads.models import Record

from .models import Booking, RepresentativeBooking


def _status_variants(value):
    variants = {value}
    try:
        variants.add(value.encode("utf-8").decode("cp1251"))
    except Exception:
        pass
    try:
        variants.add(value.encode("cp1251").decode("utf-8"))
    except Exception:
        pass
    return variants


class AddEventForm(forms.ModelForm):
    client = forms.ModelChoiceField(queryset=Record.objects.none(), label="Клиент:")
    time = forms.ChoiceField(choices=(), label="Время приема:")
    employees = forms.ModelChoiceField(queryset=User.objects.none(), label="Сотрудник:")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        available_times = kwargs.pop("available_times")
        self.selected_date = kwargs.pop("selected_date")
        super().__init__(*args, **kwargs)

        self.fields["employees"].queryset = User.objects.filter(
            companys_id=self.user.companys_id,
            status__in=list(_status_variants("Юрист пирвичник")),
        )
        clients_queryset = Record.objects.filter(
            companys_id=self.user.companys_id,
            status__in=list(_status_variants("Запись в офис")),
        )
        if self.user.felial_id:
            clients_queryset = clients_queryset.filter(felial_id=self.user.felial_id)
        self.fields["client"].queryset = clients_queryset
        self.fields["time"].choices = [(t, t) for t in available_times if t != "none"]

    class Meta:
        model = Booking
        fields = ["client", "employees", "time"]


class AddRepresentativeEventForm(forms.ModelForm):
    destination = forms.CharField(max_length=255, label="Куда идет:")
    client = forms.ModelChoiceField(queryset=Record.objects.none(), label="По какому клиенту:")
    time = forms.ChoiceField(choices=(), label="На какое время:")
    representative = forms.ModelChoiceField(queryset=User.objects.none(), label="Какой представитель:")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        available_times = kwargs.pop("available_times")
        self.selected_date = kwargs.pop("selected_date")
        super().__init__(*args, **kwargs)

        self.fields["representative"].queryset = User.objects.filter(
            companys_id=self.user.companys_id,
            status__in=list(_status_variants("Представитель")),
        ).order_by("username")

        clients_queryset = Record.objects.filter(
            companys_id=self.user.companys_id,
            representative=True,
        ).order_by("-created_at")
        if self.user.felial_id:
            clients_queryset = clients_queryset.filter(felial_id=self.user.felial_id)
        self.fields["client"].queryset = clients_queryset
        self.fields["time"].choices = [(t, t) for t in available_times if t != "none"]

    class Meta:
        model = RepresentativeBooking
        fields = ["destination", "client", "time", "representative"]
