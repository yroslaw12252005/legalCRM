from django.shortcuts import redirect, render
from django.contrib import messages
from django.shortcuts import render
from datetime import datetime, time, timedelta
from datetime import date

from .models import Booking
from accounts.models import User
from cost.models import Surcharge

from .forms import AddEventForm

from datetime import datetime, time
def smart_calendar(request):
    # Обработка даты
    selected_date = datetime.today().date()
    if 'date' in request.GET:
        try:
            selected_date = datetime.strptime(request.GET['date'], '%Y-%m-%d').date()

        except ValueError:
            pass



    start_dat = datetime.combine(selected_date, time.min)
    end_dat = datetime.combine(selected_date, time.max)

    surcharges = Surcharge.objects.filter(dat__range=(start_dat, end_dat))

    get_all_employees = User.objects.filter(companys=request.user.companys, felial=request.user.felial)

    # Навигация по датам
    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)

    bookings = Booking.objects.filter(
        date=selected_date,
        companys=request.user.companys, felial=request.user.felial
    ).order_by('time')

    context = {
        'bookings': bookings,
        'selected_date': selected_date,
        'previous_date': prev_date,
        'next_date': next_date,
        'surcharges':surcharges,
        'users':get_all_employees,
    }
    return render(request, 'calendar.html', context)



def add_event(request, pk):
    # Получаем выбранную дату из pk (предполагается формат YYYYMMDD)

    selected_date = pk


    # Генерируем временные слоты и исключаем занятые
    TIME_CHOICES = [(f"{h:02}:{m:02}") for h in range(9, 19) for m in (0, 15, 30, 45)]

    for t in TIME_CHOICES:
        if Booking.objects.filter(date=selected_date, time=t):
            TIME_CHOICES[TIME_CHOICES.index(t)]="none"


    # Передаем параметры в форму
    form = AddEventForm(
        user=request.user,
        available_times=TIME_CHOICES,
        selected_date=selected_date,
        data=request.POST or None
    )

    if request.user.is_authenticated and request.method == "POST":
        if form.is_valid():
            event = form.save(commit=False)
            if Booking.objects.filter(client_id=event.client).exists():
                messages.success(request, "Этот клиент уже записан удалите предыдущую запись")
                return redirect("calendar")
            else:
                event = form.save(commit=False)
                event.companys = request.user.companys
                event.felial = request.user.felial
                event.date = selected_date
                event.save()
                messages.success(request, "Запись успешно создана")
                return redirect("calendar")  # Измените на нужный роут

    return render(request, "add_event.html", {"form": form})


def delete_come(request, pk):
    if request.user.is_authenticated:
        del_come = Booking.objects.get(client_id=pk)
        del_come.delete()
        messages.success(request, "Вы спешно удалил запись на прием")
        return redirect("home")
    else:
        return redirect("home")