from django import forms

from accounts.models import User
from leads.models import Record

from .models import Booking, RepresentativeBooking, CallBooking


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


def _status_matches(value, *targets):
    if not value:
        return False
    variants = _status_variants(value)
    for target in targets:
        if variants & _status_variants(target):
            return True
    return False


class AddCallEventForm(forms.ModelForm):
    date = forms.DateField(
        label="Дата созвона",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    time = forms.ChoiceField(choices=(), label="Время созвона")
    employees = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Юрист первичник",
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        time_choices = [(f"{h:02}:{m:02}", f"{h:02}:{m:02}") for h in range(9, 19) for m in (0, 15, 30, 45)]
        self.fields["time"].choices = time_choices

        lawyers_qs = User.objects.filter(
            companys_id=self.user.companys_id,
            status__in=list(_status_variants("Юрист пирвичник")),
        ).order_by("username")
        if self.user.felial_id:
            lawyers_qs = lawyers_qs.filter(felial_id=self.user.felial_id)

        self.fields["employees"].queryset = lawyers_qs

        is_director_upp = _status_matches(self.user.status, "Директор ЮПП")
        if is_director_upp:
            self.fields["employees"].required = True
        else:
            self.fields.pop("employees")

    class Meta:
        model = CallBooking
        fields = ["date", "time", "employees"]


class AddOfficeBookingFromRecordForm(forms.ModelForm):
    date = forms.DateField(
        label="Дата записи",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    time = forms.ChoiceField(choices=(), label="Время записи")
    employees = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Юрист первичник",
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        time_choices = [(f"{h:02}:{m:02}", f"{h:02}:{m:02}") for h in range(9, 19) for m in (0, 15, 30, 45)]
        self.fields["time"].choices = time_choices

        lawyers_qs = User.objects.filter(
            companys_id=self.user.companys_id,
            status__in=list(_status_variants("Юрист пирвичник")),
        ).order_by("username")
        if self.user.felial_id:
            lawyers_qs = lawyers_qs.filter(felial_id=self.user.felial_id)
        self.fields["employees"].queryset = lawyers_qs

        can_choose = _status_matches(
            self.user.status,
            "Директор ЮПП",
            "Директор КЦ",
            "Оператор",
            "Менеджер",
            "Администратор",
        )
        if can_choose:
            self.fields["employees"].required = True
        else:
            self.fields.pop("employees")

    class Meta:
        model = Booking
        fields = ["date", "time", "employees"]
