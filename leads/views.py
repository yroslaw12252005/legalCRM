from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from .models import Record
from todolist.models import ToDoList
from coming.models import Coming
from django.db.models import Sum
from cost.models import Cost
from cost.models import Surcharge
from accounts.models import User

from .forms import AddRecordForm, StatusForm, Employees_KCForm, Employees_UPPForm, Cost_form

import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import datetime

from django.views.decorators.csrf import csrf_exempt

def home(request):
    current_time = datetime.datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    now = f"{year}-{month}-{day}"
    todolist = ToDoList.objects.all()
    records = Record.objects.all()
    coming = Coming.objects.all()
    user  =  User.objects.all()
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
        ##cost_upp = Record.objects.aggregate(Sum('caunt'))
        #items = Cost.objects.all()
        #cost_upp = 0
        #if request.user.is_authenticated:

        #    if request.user.status == "Юрист пирвичник":
        #        items = items.filter( employees_UPP = request.user.username)
        #        cost_upp = sum(items.values_list('caunt', flat=True))
        #    else:
        #        cost_upp = sum(items.values_list('caunt', flat=True))

        return render(request, "home.html", {"records": records, 'users':user, 'todolist':todolist, "comings":coming, "now":now})

def filter(request, status):
    records = Record.objects.all()
    return render(request, "filter.html",
                  {"records": records, "status":status})

def brak(request):
    records = Record.objects.filter(status="Брак")
    return render(request, "home.html", {"record": records})

def logout_user(request):
    logout(request)
    return redirect("home")

def record(request, pk):
    if request.user.is_authenticated:
        cost = Cost.objects.filter(record_id=pk)
        record = Record.objects.get(id=pk)
        surcharge = Surcharge.objects.filter(record_id=pk)
        form_status = StatusForm(request.POST or None, instance=record)
        form_employees_KC = Employees_KCForm(request.POST or None, instance=record)
        form_employees_UPP = Employees_UPPForm(request.POST or None, instance=record)
        cost_form = Cost_form(request.POST or None)
        if form_status.is_valid():
            form_status.save()
            messages.success(request, f"Статус был успешно обнавлена")
            return redirect("home")

        elif form_employees_KC.is_valid():
            form_employees_KC.save()
            messages.success(request, f"Оператор прикреплен")
            return redirect("home")

        elif form_employees_UPP.is_valid():
            form_employees_UPP.save()
            messages.success(request, f"Юрист прикреплен")
            return redirect("home")

        elif  cost_form.is_valid():
            cost =  cost_form.save(commit=False)
            if  cost_form.record_id == "null":
                 cost_form.record_id = pk
                 cost_form.save()
            else:
               a = Cost.objects.get(record_id=pk)
               a.cost = cost.cost
               a.save()

            messages.success(request, f"Цена указана")
            return redirect("home")


        return render(request, "record.html", {"record": record, "form_status":form_status, "form_employees_KC":form_employees_KC, "form_employees_UPP":form_employees_UPP, "cost":cost, "surcharge":surcharge})
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
    form = AddRecordForm(request.POST or None)
    if request.user.is_authenticated:
        if form.is_valid():
            add_record = form.save(commit=False)
            add_record.companys = request.user.companys  # The logged-in user
            add_record.save()
            messages.success(request, f"Заявка  с именем {add_record.name} успешно создана")
            return redirect("home")
        return render(request, "add_record.html", {"form": form})
    else:
        return redirect("home")

def update_record(request, pk):
    if request.user.is_authenticated:
        record = Record.objects.get(id=pk)
        form = AddRecordForm(request.POST or None, instance=record)
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
        return HttpResponse("test")
    else:
        data = request.POST
        phone = None
        name = None
        textarea = None

        for key, value in data.items():
            if key == "Phone":
                phone = value
            elif key == "Name":
                name = value
            elif key == "Textarea":
                textarea = value

        led = Record(phone=phone, name=name,  description=textarea)
        led.save()
        return HttpResponse(200)

def search_results(request):
    return HttpResponse(request.POST)