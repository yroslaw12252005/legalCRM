from django import template
import calendar
from datetime import date, datetime, timedelta
from smart_calendar.models import Booking

register = template.Library()


@register.inclusion_tag('mini_calendar.html')
def mini_calendar():
    today = date.today()
    year, month = today.year, today.month
    cal = calendar.Calendar(firstweekday=7)  # Воскресенье первый день
    month_days = cal.monthdayscalendar(year, month)

    # Определение границ месяца
    start_date = date(year, month, 1)
    end_date = start_date + timedelta(days=31)

    # Получение всех записей, пересекающихся с текущим месяцем
    bookings = Booking.objects.filter(
        start_time__lt=end_date,
        end_time__gte=start_date
    )

    # Подсчет записей для каждого дня
    bookings_per_day = {}
    for booking in bookings:
        current_day = booking.start_time.date()
        end_day = booking.end_time.date()
        while current_day <= end_day:
            if start_date <= current_day < end_date:
                day_key = current_day.day
                bookings_per_day[day_key] = bookings_per_day.get(day_key, 0) + 1
            current_day += timedelta(days=1)

    # Форматирование данных для шаблона
    formatted_weeks = []
    for week in month_days:
        formatted_week = []
        for day in week:
            count = bookings_per_day.get(day, 0) if day != 0 else 0
            formatted_week.append({'day': day,'year':year, 'month':month, 'count': count})
        formatted_weeks.append(formatted_week)

    return {
        'month_name': f"{calendar.month_name[month]} {year}",
        'header': ['П', 'В', 'С', 'Ч', 'П', 'С', 'В'],
        'weeks': formatted_weeks,
        'today': today.day
    }
