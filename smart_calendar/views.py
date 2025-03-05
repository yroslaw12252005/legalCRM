from django.shortcuts import redirect, render
from django.contrib import messages
from django.shortcuts import render
from datetime import datetime, time, timedelta
from datetime import date

from .models import Booking
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

    # Навигация по датам
    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)

    # Получение записей
    start_datetime = datetime.combine(selected_date, time.min)
    end_datetime = datetime.combine(selected_date, time.max)
    bookings = Booking.objects.filter(
        start_time__gte=start_datetime,
        end_time__lte=end_datetime
    ).order_by('start_time')

    context = {
        'bookings': bookings,
        'selected_date': selected_date,
        'previous_date': prev_date,
        'next_date': next_date,
        'surcharges':surcharges,
    }
    return render(request, 'calendar.html', context)



def add_event(request):
    form = AddEventForm(request.POST or None)
    if request.user.is_authenticated:
        if form.is_valid():
            event = form.save()
            messages.success(request, f"Запись на прием {event.client} успешно создана")
            return redirect("home")
        return render(request, "add_event.html", {"form": form})
    else:
        return redirect("home")