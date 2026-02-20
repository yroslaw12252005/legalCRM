from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from cost.models import Surcharge

from .forms import AddEventForm
from .models import Booking


@login_required
def smart_calendar(request):
    if request.user.status == "ОП":
        messages.warning(request, "Доступ к календарю ограничен")
        return redirect("home")

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

    if request.user.status in {"Администратор", "Менеджер", "Директор ЮПП", "Директор КЦ"}:
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
    if request.user.status in {"Администратор", "Менеджер", "Директор ЮПП"}:
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
def add_event(request, pk):
    selected_date = pk
    time_choices = [(f"{h:02}:{m:02}") for h in range(9, 19) for m in (0, 15, 30, 45)]

    busy_times = set(Booking.objects.filter(date=selected_date).values_list("time", flat=True))
    available_times = [t for t in time_choices if t not in busy_times]

    form = AddEventForm(
        user=request.user,
        available_times=available_times,
        selected_date=selected_date,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        if Booking.objects.filter(client_id=event.client_id).exists():
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
