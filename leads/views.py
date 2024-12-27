from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse

from .models import Record
from todolist.models import ToDoList
from coming.models import Coming
from .forms import AddRecordForm, StatusForm, Employees_KCForm, Employees_UPPForm
from accounts.models import User

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
    print(now)
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
        return render(request, "home.html", {"records": records, 'users':user, 'todolist':todolist, "comings":coming, "now":now})

def filter(request, status):
    records = Record.objects.all()
    return render(request, "filter.html",
                  {"records": records, "status":status})

def logout_user(request):
    logout(request)
    return redirect("home")

def record(request, pk):
    if request.user.is_authenticated:
        record = Record.objects.get(id=pk)
        form_status = StatusForm(request.POST or None, instance=record)
        form_employees_KC = Employees_KCForm(request.POST or None, instance=record)
        form_employees_UPP = Employees_UPPForm(request.POST or None, instance=record)
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

        return render(request, "record.html", {"record": record, "form_status":form_status, "form_employees_KC":form_employees_KC, "form_employees_UPP":form_employees_UPP})
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
            add_record = form.save()
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
    data = request.POST
    led = Record.objects.get(id=2)
    led.phone = data['Phone']
    led.save()
    return HttpResponse("test")