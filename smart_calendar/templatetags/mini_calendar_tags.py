from django import template
import calendar
from datetime import date, datetime, timedelta
from smart_calendar.models import Booking
from cost.models import Surcharge
from collections import defaultdict

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

register = template.Library()

@csrf_exempt
@require_POST
@register.inclusion_tag('mini_calendar.html')
def mini_calendar(employee_id, employee_status):
    today = date.today()
   #if request.method == "POST":
   #    today = request.POST['date']
    year, month = today.year, today.month
    cal = calendar.Calendar(firstweekday=7)
    month_days = cal.monthdayscalendar(year, month)

    # Границы месяца
    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=31)).replace(day=1)
    if employee_status == "Менеджер" or employee_status == "Администратор" or employee_status == "Директор ЮПП" or employee_status == "Директор КЦ":
        # Получение данных
        bookings = Booking.objects.filter(
            date__lt=end_date,
            date__gte=start_date
        )

        # Исправленный фильтр для доплат
        surcharges = Surcharge.objects.filter(dat__range=(start_date, end_date))
    else:
        if employee_status != "Юрист пирвичник":
            bookings = Booking.objects.filter(
                date__lt=end_date,
                date__gte=start_date,
                registrar=employee_id
            )
        else:
            bookings = Booking.objects.filter(
                date__lt=end_date,
                date__gte=start_date,
                employees=employee_id
            )


        # Исправленный фильтр для доплат
        surcharges = Surcharge.objects.filter(dat__range=(start_date, end_date), responsible=employee_id)

    # Подсчет доплат
    surcharges_per_day = defaultdict(int)
    for surcharge in surcharges:
        current_day = surcharge.dat.date()
        if start_date <= current_day < end_date:
            surcharges_per_day[current_day.day] += 1

    # Подсчет бронирований
    bookings_per_day = defaultdict(int)
    for booking in bookings:
        current_day = booking.date
        if start_date <= current_day < end_date:
            bookings_per_day[current_day.day] += 1
        current_day += timedelta(days=1)

    # Форматирование данных
    formatted_weeks = []
    for week in month_days:
        formatted_week = []
        for day in week:
            formatted_week.append({
                'day': day,
                'year': year,
                'month': month,
                'count': bookings_per_day.get(day, 0),
                'surcharges_count': surcharges_per_day.get(day, 0)
            })
        formatted_weeks.append(formatted_week)

    return {
        'month_name': f"{calendar.month_name[month]} {year}",
        'header': ['П', 'В', 'С', 'Ч', 'П', 'С', 'В'],
        'weeks': formatted_weeks,
        'today': today.day
    }
