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

    # Получение записей
    start_datetime = datetime.combine(selected_date, time.min)
    end_datetime = datetime.combine(selected_date, time.max)
    bookings = Booking.objects.filter(
        start_time__gte=start_datetime,
        end_time__lte=end_datetime,
        companys=request.user.companys, felial=request.user.felial
    ).order_by('start_time')

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
    booked_times = Booking.objects.filter(start_time__date=selected_date).values_list('start_time__time', flat=True)
    available_times = [t for t in TIME_CHOICES if datetime.strptime(t, "%H:%M").time() not in booked_times]

    # Передаем параметры в форму
    form = AddEventForm(
        user=request.user,
        available_times=available_times,
        selected_date=selected_date,
        data=request.POST or None
    )

    if request.user.is_authenticated and request.method == "POST":
        if form.is_valid():
            event = form.save(commit=False)
            event.companys = request.user.companys
            event.felial = request.user.felial
            event.save()
            messages.success(request, "Запись успешно создана")
            return redirect("calendar_view")  # Измените на нужный роут

    return render(request, "add_event.html", {"form": form})