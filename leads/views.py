from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView, ListView
from django.db.models import Q

from accounts.views import employees
from felial.views import felials

from .models import Record
from todolist.models import ToDoList
from django.db.models import Sum
from cost.models import Surcharge
from accounts.models import User
from smart_calendar.models import Booking

from .forms import AddRecordForm, StatusForm, Employees_KCForm, Employees_UPPForm, CostForm

import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import datetime

from django.views.decorators.csrf import csrf_exempt

from django import template
import calendar
from datetime import date, datetime, timedelta
from smart_calendar.models import Booking
from cost.models import Surcharge
from collections import defaultdict

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

def home(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                messages.warning(request, "Не правельный логин или пароль")
                return redirect("home")
        else:
            return render(request, "home.html")
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    now = f"{year}-{month}-{day}"
    todolist = ToDoList.objects.all()
    get_records = Record.objects.filter(companys=request.user.companys, felial=request.user.felial)
    user  =  User.objects.all()
    return render(request, "home.html", {"records": get_records, 'users':user, 'todolist':todolist, "now":now})

def filter(request, status):
    records = Record.objects.filter(status=status, companys=request.user.companys, felial=request.user.felial)
    return render(request, "home.html", {"records": records})

def brak(request):
    records = Record.objects.filter(status="Брак")
    return render(request, "home.html", {"records": records})

def logout_user(request):
    logout(request)
    return redirect("home")

def record(request, pk):
    if request.user.is_authenticated:
        record = Record.objects.get(id=pk)
        surcharge = Surcharge.objects.filter(record_id=pk)
        form_status = StatusForm(request.POST or None, instance=record)
        form_employees_KC = Employees_KCForm(request.POST or None, instance=record)
        form_employees_UPP = Employees_UPPForm(request.POST or None, instance=record)
        cost_form = CostForm(request.POST or None, instance=record)
        get_status_com = 0
        if Booking.objects.filter(client_id=pk).exists():
            get_status_com = Booking.objects.get(client_id=pk)

        if form_status.is_valid():
            form_status.save()
            messages.success(request, f"Статус был успешно обнавлена")
            return render(request, "record.html",
                          {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                           "form_employees_UPP": form_employees_UPP, "cost": cost_form, "surcharge": surcharge})

        elif form_employees_KC.is_valid():
            form_employees_KC.save()
            messages.success(request, f"Оператор прикреплен")
            return render(request, "record.html",
                          {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                           "form_employees_UPP": form_employees_UPP, "cost": cost_form, "surcharge": surcharge})

        elif form_employees_UPP.is_valid():
            form_employees_UPP.save()
            messages.success(request, f"Юрист прикреплен")
            return render(request, "record.html",
                          {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                           "form_employees_UPP": form_employees_UPP, "cost": cost_form, "surcharge": surcharge,
                           })


        elif  cost_form.is_valid():
            cost_form.save()
            messages.success(request, f"Цена указана")
            return render(request, "record.html",
                          {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                           "form_employees_UPP": form_employees_UPP, "cost": cost_form, "surcharge": surcharge,
                         })

        return render(request, "record.html", {"record": record,"get_status_com":get_status_com, "form_status":form_status, "form_employees_KC":form_employees_KC, "form_employees_UPP":form_employees_UPP, "cost":cost_form, "surcharge":surcharge})
    else:
        return redirect("home")

def delete_record(request, pk):
    if request.user.is_authenticated:
        del_record = Record.objects.get(id=pk)
        del_record.delete()
        messages.success(request, "Вы спешно удалил запись")
        return redirect("home")
    else:
        return redirect("home")

def add_record(request):
    form = AddRecordForm(request.POST or None, user=request.user)
    if request.user.is_authenticated:
        if form.is_valid():
            add_record = form.save(commit=False)
            add_record.companys = request.user.companys
            if request.user.status =="Оператор":
                add_record.employees_KC = request.user.username
             # Прикрепляется к крмпании
            add_record.save()
            messages.success(request, f"Заявка  с именем {add_record.name} успешно создана")
            return redirect("home")
        return render(request, "add_record.html", {"form": form})
    else:
        return redirect("home")

def update_record(request, pk):
    if request.user.is_authenticated:
        record = Record.objects.get(id=pk)
        form = AddRecordForm(request.POST or None, instance=record,  user=request.user)
        if form.is_valid():
            updated_record = form.save()
            messages.success(request, f"Запись '{updated_record.name}' обнавлена")
            return redirect("home")
        return render(request, "update_record.html", {"form": form})
    else:
        messages.error(request, "You have to login")
        return redirect("home")

def in_work(request, pk):
    record = Record.objects.get(id=pk)
    record.in_work = 1
    record.save()
    return redirect("home")

@csrf_exempt
@require_POST
def get_tilda_lead(request):
    if request.POST.get('test', False):
        print(200)
        return HttpResponse("test")
    else:
        data = request.POST
        phone = None
        name = None
        textarea = None
        print(data.items())
        for key, value in data.items():
            if key == "Phone":
                phone = value
            elif key == "Name":
                name = value
            elif key == "Textarea":
                textarea = value

        led = Record(phone=phone, name=name,  description=textarea, where="Tilda")
        led.save()
        print(200)
        return HttpResponse(200)

class SearchView(ListView):
    model = Record
    template_name = 'search_results.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        return Record.objects.filter(
            Q(name__icontains=query) |  # Поиск по части имени
            Q(phone__icontains=query)
        )

@csrf_exempt
@require_POST
def get_time(request):
    import locale
    locale.setlocale(locale.LC_ALL, 'C.utf8')
    if request.method == "POST":
        employee_id = request.user.id
        employee_status = request.user.status
        today = date.today()
        if request.method == "POST":
           today = request.POST['date']
           today = datetime.strptime(today, '%Y-%m-%d')
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

        return render(request, "mini_calendar.html", {
            'month_name': f"{calendar.month_name[month]} {year}",
            'header': ['П', 'В', 'С', 'Ч', 'П', 'С', 'В'],
            'weeks': formatted_weeks,
            'today': today.day
        })
    return HttpResponse("Метод не разрешён", status=405)