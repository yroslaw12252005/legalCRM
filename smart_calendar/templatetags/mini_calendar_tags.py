from django import template
from django.utils import timezone
import calendar

register = template.Library()


@register.inclusion_tag('mini_calendar.html')
def mini_calendar():
    now = timezone.now()
    year = now.year
    month = now.month
    cal = calendar.Calendar(firstweekday=7)  # Воскресенье первый день
    month_days = cal.monthdayscalendar(year, month)

    # Форматируем заголовок
    month_name = calendar.month_name[month]
    header = ['П', 'В', 'С', 'Ч', 'П', 'С', 'В']

    return {
        'year':year,
        'month_name': f"{month_name} {year}",
        'header': header,
        'weeks': month_days,
        'current_month': month
    }

