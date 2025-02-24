from django.shortcuts import render
from django.utils import timezone
from .models import Event
from .form import AddEventForm
import calendar

def calendar_view(request):
    # Получение и корректировка месяца/года
    try:
        month = int(request.GET.get('month', timezone.now().month))
    except ValueError:
        month = timezone.now().month

    try:
        year = int(request.GET.get('year', timezone.now().year))
    except ValueError:
        year = timezone.now().year

    # Корректировка некорректных значений
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1

    # Расчет предыдущего и следующего месяцев
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    # Генерация календаря
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdays2calendar(year, month)

    # Получение событий
    events = Event.objects.filter(
        time__year=year,
        time__month=month
    ).order_by('time')

    events_by_day = {}
    for event in events:
        day = event.time.day
        events_by_day.setdefault(day, []).append(event)

    context = {
        'month_days': month_days,
        'events_by_day': events_by_day,
        'current_month': month,
        'current_year': year,
        'month_name': calendar.month_name[month],
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }
    return render(request, 'calendar.html', context)



def add_event(request):
    form = AddEventForm(request.POST or None)
    if request.user.is_authenticated:
        if form.is_valid():
            add_record = form.save()
            return redirect("home")
        return render(request, "add_event.html", {"form": form})
    else:
        return redirect("home")