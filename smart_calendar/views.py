from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from cost.models import Surcharge
from leads.models import Record

from .forms import AddRepresentativeEventForm, AddCallEventForm, AddOfficeBookingFromRecordForm
from .models import Booking, RepresentativeBooking, CallBooking

STATUS_OP = "ОП"
STATUS_ADMIN = "Администратор"
STATUS_MANAGER = "Менеджер"
STATUS_DIRECTOR_UPP = "Директор ЮПП"
STATUS_DIRECTOR_KC = "Директор КЦ"
STATUS_LAWYER_PRIMARY = "Юрист пирвичник"
STATUS_DIRECTOR_REP = "Директор представителей"
STATUS_REPRESENTATIVE = "Представитель"


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


STATUS_DIRECTOR_UPP_RU = "Директор ЮПП"
STATUS_LAWYER_PRIMARY_RU = "Юрист пирвичник"
STATUS_ADMIN_RU = "Администратор"
STATUS_MANAGER_RU = "Менеджер"
STATUS_DIRECTOR_KC_RU = "Директор КЦ"


def _status_matches(value, *targets):
    if not value:
        return False
    variants = _status_variants(value)
    for target in targets:
        if variants & _status_variants(target):
            return True
    return False


def _is_representative_role(user):
    return user.status in _status_variants(STATUS_DIRECTOR_REP) or user.status in _status_variants(STATUS_REPRESENTATIVE)


def _can_manage_call_booking(user):
    return _status_matches(user.status, STATUS_LAWYER_PRIMARY_RU, STATUS_DIRECTOR_UPP_RU)


def _can_choose_call_lawyer(user):
    return _status_matches(user.status, STATUS_DIRECTOR_UPP_RU)


def _can_manage_office_booking(user):
    return _status_matches(
        user.status,
        STATUS_LAWYER_PRIMARY_RU,
        "Директор ЮПП",
        "Директор КЦ",
        "Оператор",
        "Менеджер",
        "Администратор",
    )


def _can_choose_office_lawyer(user):
    return _status_matches(user.status, "Директор ЮПП", "Директор КЦ", "Оператор", "Менеджер", "Администратор")


@login_required
def smart_calendar(request):
    if request.user.status == STATUS_OP:
        messages.warning(request, "Доступ к календарю ограничен")
        return redirect("all_leads")
    if _is_representative_role(request.user):
        messages.info(request, "Для вашей роли доступен календарь судов и инстанций")
        return redirect("representative_calendar")

    selected_date = datetime.today().date()
    if "date" in request.GET:
        try:
            selected_date = datetime.strptime(request.GET["date"], "%Y-%m-%d").date()
        except ValueError:
            pass

    start_dat = datetime.combine(selected_date, time.min)
    end_dat = datetime.combine(selected_date, time.max)

    can_view_all_surcharges = _status_matches(
        request.user.status,
        "Администратор",
        "Менеджер",
        "Директор ЮПП",
    )
    if can_view_all_surcharges:
        get_all_employees = User.objects.filter(companys=request.user.companys)
    else:
        get_all_employees = User.objects.filter(companys=request.user.companys, felial=request.user.felial)
    lawyers = get_all_employees.filter(status__in=list(_status_variants(STATUS_LAWYER_PRIMARY_RU)))

    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)

    is_operator = _status_matches(request.user.status, "Оператор")
    can_view_all_office_bookings = _status_matches(
        request.user.status,
        "Администратор",
        "Менеджер",
        "Директор ЮПП",
        "Директор КЦ",
    )
    can_view_all_call_bookings = _status_matches(request.user.status, "Администратор", "Директор ЮПП", "Менеджер")

    if can_view_all_office_bookings:
        bookings = Booking.objects.filter(
            date=selected_date,
            companys=request.user.companys,
            felial=request.user.felial,
        ).order_by("time")
        if can_view_all_call_bookings:
            call_bookings = CallBooking.objects.filter(
                date=selected_date,
                companys=request.user.companys,
                felial=request.user.felial,
            ).order_by("time")
        else:
            call_bookings = CallBooking.objects.none()
    elif _status_matches(request.user.status, STATUS_LAWYER_PRIMARY_RU):
        bookings = Booking.objects.filter(
            date=selected_date,
            companys=request.user.companys,
            felial=request.user.felial,
            employees=request.user.id,
        ).order_by("time")
        call_bookings = CallBooking.objects.filter(
            date=selected_date,
            companys=request.user.companys,
            felial=request.user.felial,
            employees=request.user.id,
        ).order_by("time")
        lawyers = lawyers.filter(id=request.user.id)
    elif is_operator:
        bookings = Booking.objects.filter(
            date=selected_date,
            companys=request.user.companys,
            felial=request.user.felial,
            client__employees_KC=request.user.username,
        ).order_by("time")
        call_bookings = CallBooking.objects.none()
    else:
        bookings = Booking.objects.filter(
            date=selected_date,
            companys=request.user.companys,
            felial=request.user.felial,
            registrar=request.user.id,
        ).order_by("time")
        call_bookings = CallBooking.objects.none()

    surcharges = None
    if can_view_all_surcharges:
        surcharges = Surcharge.objects.filter(
            dat__range=(start_dat, end_dat),
            record__companys=request.user.companys,
        ).select_related("record").order_by("dat")
    elif _status_matches(request.user.status, "Юрист пирвичник"):
        surcharges = Surcharge.objects.filter(
            dat__range=(start_dat, end_dat),
            record__companys=request.user.companys,
            record__felial=request.user.felial,
            record__employees_UPP=request.user.username,
        ).select_related("record").order_by("dat")

    context = {
        "bookings": bookings,
        "call_bookings": call_bookings,
        "selected_date": selected_date,
        "previous_date": prev_date,
        "next_date": next_date,
        "surcharges": surcharges,
        "users": get_all_employees,
        "lawyers": lawyers,
    }
    return render(request, "calendar.html", context)


@login_required
def representative_calendar(request):
    if not _is_representative_role(request.user):
        messages.warning(request, "Доступ к календарю судов и инстанций ограничен")
        return redirect("all_leads")

    selected_date = datetime.today().date()
    if "date" in request.GET:
        try:
            selected_date = datetime.strptime(request.GET["date"], "%Y-%m-%d").date()
        except ValueError:
            pass

    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)

    reps = User.objects.filter(
        companys=request.user.companys,
        status__in=list(_status_variants(STATUS_REPRESENTATIVE)),
    ).order_by("username")

    bookings = RepresentativeBooking.objects.filter(
        date=selected_date,
        companys=request.user.companys,
    )
    if request.user.status in _status_variants(STATUS_REPRESENTATIVE):
        bookings = bookings.filter(representative=request.user)
        reps = reps.filter(id=request.user.id)

    context = {
        "bookings": bookings.order_by("time"),
        "selected_date": selected_date,
        "previous_date": prev_date,
        "next_date": next_date,
        "representatives": reps,
        "can_add_event": request.user.status in _status_variants(STATUS_DIRECTOR_REP),
    }
    return render(request, "representative_calendar.html", context)


@login_required
def add_representative_event(request, pk):
    if request.user.status not in _status_variants(STATUS_DIRECTOR_REP):
        messages.warning(request, "Назначать представителя может только директор представителей")
        return redirect("representative_calendar")

    selected_date = pk
    time_choices = [(f"{h:02}:{m:02}") for h in range(9, 19) for m in (0, 15, 30, 45)]

    form = AddRepresentativeEventForm(
        user=request.user,
        available_times=time_choices,
        selected_date=selected_date,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        exists_for_rep = RepresentativeBooking.objects.filter(
            representative=event.representative,
            date=selected_date,
            time=event.time,
            companys=request.user.companys,
        ).exists()
        if exists_for_rep:
            messages.warning(request, "У выбранного представителя уже есть запись на это время")
            return redirect("representative_calendar")

        event.companys = request.user.companys
        event.felial = request.user.felial
        event.date = selected_date
        event.registrar = request.user
        event.save()
        messages.success(request, "Запись в суд/инстанцию успешно создана")
        return redirect("representative_calendar")

    return render(request, "add_representative_event.html", {"form": form})


@login_required
def add_call_event(request, pk):
    if not _can_manage_call_booking(request.user):
        messages.warning(request, "Назначать созвон может только юрист первичник или директор ЮПП")
        return redirect("record", pk=pk)

    record = get_object_or_404(Record, id=pk, companys=request.user.companys)
    if request.user.felial_id and record.felial_id and request.user.felial_id != record.felial_id:
        messages.warning(request, "Нет доступа к заявке другого филиала")
        return redirect("record", pk=pk)

    form = AddCallEventForm(
        user=request.user,
        data=request.POST or None,
        initial={"date": datetime.today().date()},
    )
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        if not _can_choose_call_lawyer(request.user):
            event.employees = request.user

        has_office_conflict = Booking.objects.filter(
            date=event.date,
            time=event.time,
            companys=request.user.companys,
            felial=record.felial,
            employees=event.employees,
        ).exists()
        has_call_conflict = CallBooking.objects.filter(
            date=event.date,
            time=event.time,
            companys=request.user.companys,
            felial=record.felial,
            employees=event.employees,
        ).exists()
        if has_office_conflict or has_call_conflict:
            messages.warning(request, "У выбранного юриста уже есть событие на это время")
            return render(request, "add_call_event.html", {"form": form, "record": record})

        event.client = record
        event.companys = request.user.companys
        event.felial = record.felial or request.user.felial
        event.registrar = request.user
        event.save()
        messages.success(request, "Созвон успешно назначен")
        return redirect("record", pk=record.id)

    return render(request, "add_call_event.html", {"form": form, "record": record})


@login_required
def add_office_booking(request, pk):
    if not _can_manage_office_booking(request.user):
        messages.warning(request, "Недостаточно прав для записи в офис")
        return redirect("record", pk=pk)

    record = get_object_or_404(Record, id=pk, companys=request.user.companys)

    form = AddOfficeBookingFromRecordForm(
        user=request.user,
        data=request.POST or None,
        initial={"date": datetime.today().date()},
    )
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        if not _can_choose_office_lawyer(request.user):
            event.employees = request.user

        if Booking.objects.filter(client_id=record.id, companys=request.user.companys).exists():
            messages.warning(request, "Этот клиент уже записан в офис, удалите старую запись перед новой")
            return redirect("record", pk=record.id)

        has_office_conflict = Booking.objects.filter(
            date=event.date,
            time=event.time,
            companys=request.user.companys,
            felial=record.felial,
            employees=event.employees,
        ).exists()
        has_call_conflict = CallBooking.objects.filter(
            date=event.date,
            time=event.time,
            companys=request.user.companys,
            felial=record.felial,
            employees=event.employees,
        ).exists()
        if has_office_conflict or has_call_conflict:
            messages.warning(request, "У выбранного юриста уже есть событие на это время")
            return render(request, "add_office_booking.html", {"form": form, "record": record})

        event.client = record
        event.companys = request.user.companys
        event.felial = record.felial or request.user.felial
        event.registrar = request.user
        event.save()
        messages.success(request, "Клиент успешно записан в офис")
        return redirect("record", pk=record.id)

    return render(request, "add_office_booking.html", {"form": form, "record": record})


@login_required
def delete_come(request, pk):
    del_come = get_object_or_404(Booking, client_id=pk, companys=request.user.companys)
    del_come.delete()
    messages.success(request, "Вы успешно удалили запись на прием")
    return redirect("all_leads")


@login_required
def come_True(request, pk):
    bookin = get_object_or_404(Booking, client_id=pk, companys=request.user.companys)
    bookin.come = 1
    bookin.save()
    return redirect("all_leads")


@login_required
def come_False(request, pk):
    bookin = get_object_or_404(Booking, client_id=pk, companys=request.user.companys)
    bookin.come = 0
    bookin.save()
    return redirect("all_leads")
