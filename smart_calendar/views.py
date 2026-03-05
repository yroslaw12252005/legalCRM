from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from cost.models import Surcharge

from .forms import AddEventForm, AddRepresentativeEventForm
from .models import Booking, RepresentativeBooking

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


def _is_representative_role(user):
    return user.status in _status_variants(STATUS_DIRECTOR_REP) or user.status in _status_variants(STATUS_REPRESENTATIVE)


@login_required
def smart_calendar(request):
    if request.user.status == STATUS_OP:
        messages.warning(request, "Доступ к календарю ограничен")
        return redirect("home")
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

    get_all_employees = User.objects.filter(companys=request.user.companys, felial=request.user.felial)

    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)

    if request.user.status in {STATUS_ADMIN, STATUS_MANAGER, STATUS_DIRECTOR_UPP, STATUS_DIRECTOR_KC}:
        bookings = Booking.objects.filter(
            date=selected_date,
            companys=request.user.companys,
            felial=request.user.felial,
        ).order_by("time")
    else:
        bookings = Booking.objects.filter(
            date=selected_date,
            companys=request.user.companys,
            felial=request.user.felial,
            registrar=request.user.id,
        ).order_by("time")

    surcharges = None
    if request.user.status in {STATUS_ADMIN, STATUS_MANAGER, STATUS_DIRECTOR_UPP}:
        surcharges = Surcharge.objects.filter(
            dat__range=(start_dat, end_dat),
            record__companys=request.user.companys,
            record__felial=request.user.felial,
        ).order_by("dat")

    context = {
        "bookings": bookings,
        "selected_date": selected_date,
        "previous_date": prev_date,
        "next_date": next_date,
        "surcharges": surcharges,
        "users": get_all_employees,
    }
    return render(request, "calendar.html", context)


@login_required
def representative_calendar(request):
    if not _is_representative_role(request.user):
        messages.warning(request, "Доступ к календарю судов и инстанций ограничен")
        return redirect("home")

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
def add_event(request, pk):
    if _is_representative_role(request.user):
        messages.warning(request, "Календарь записей в офис для вашей роли скрыт")
        return redirect("representative_calendar")

    selected_date = pk
    time_choices = [(f"{h:02}:{m:02}") for h in range(9, 19) for m in (0, 15, 30, 45)]

    busy_times = set(
        Booking.objects.filter(
            date=selected_date,
            companys=request.user.companys,
            felial=request.user.felial,
        ).values_list("time", flat=True)
    )
    available_times = [t for t in time_choices if t not in busy_times]

    form = AddEventForm(
        user=request.user,
        available_times=available_times,
        selected_date=selected_date,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        if Booking.objects.filter(client_id=event.client_id, companys=request.user.companys).exists():
            messages.success(request, "Этот клиент уже записан, удалите предыдущую запись")
            return redirect("calendar")

        event.companys = request.user.companys
        event.felial = request.user.felial
        event.date = selected_date
        event.registrar = request.user
        event.save()
        messages.success(request, "Запись успешно создана")
        return redirect("calendar")

    return render(request, "add_event.html", {"form": form})


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
def delete_come(request, pk):
    del_come = get_object_or_404(Booking, client_id=pk, companys=request.user.companys)
    del_come.delete()
    messages.success(request, "Вы успешно удалили запись на прием")
    return redirect("home")


@login_required
def come_True(request, pk):
    bookin = get_object_or_404(Booking, client_id=pk, companys=request.user.companys)
    bookin.come = 1
    bookin.save()
    return redirect("home")


@login_required
def come_False(request, pk):
    bookin = get_object_or_404(Booking, client_id=pk, companys=request.user.companys)
    bookin.come = 0
    bookin.save()
    return redirect("home")
