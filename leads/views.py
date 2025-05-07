from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django import template

from accounts.views import employees
from company.views import companys
from felial.views import felials

from .models import Record
from todolist.models import ToDoList
from django.db.models import Sum
from cost.models import Surcharge
from accounts.models import User
from smart_calendar.models import Booking
from smart_calendar.models import Booking
from cost.models import Surcharge

from .forms import AddRecordForm, StatusForm, Employees_KCForm, Employees_UPPForm, CostForm,FileUploadForm

import asyncio
from contextlib import asynccontextmanager
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
import os
import json
import datetime
import calendar
from datetime import date, datetime, timedelta
from collections import defaultdict

from asgiref.sync import sync_to_async
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

import asyncio
from contextlib import asynccontextmanager

from aiobotocore.session import get_session
from botocore.exceptions import ClientError


class S3Client:
    def __init__(
            self,
            access_key: str,
            secret_key: str,
            endpoint_url: str,
            bucket_name: str,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "region_name": "ru-1"
        }
        self.bucket_name = bucket_name
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_file(
            self,
            file_path: str, file_name
    ):
        print(file_path)# /users/artem/cat.jpg
        try:
            async with self.get_client() as client:
                with open(file_path, "rb") as file:
                    await client.put_object(
                        Bucket=self.bucket_name,
                        Key=file_name,
                        Body=file,
                    )
                print(f"File {file_name} uploaded to {self.bucket_name}")
        except ClientError as e:
            print(f"Error uploading file: {e}")

    async def delete_file(self, object_name: str):
        try:
            async with self.get_client() as client:
                await client.delete_object(Bucket=self.bucket_name, Key=object_name)
                print(f"File {object_name} deleted from {self.bucket_name}")
        except ClientError as e:
            print(f"Error deleting file: {e}")

    async def get_file(self, object_name: str, destination_path: str):
        try:
            async with self.get_client() as client:
                response = await client.get_object(Bucket=self.bucket_name, Key=object_name)
                data = await response["Body"].read()
                with open(destination_path, "wb") as file:
                    file.write(data)
                print(f"File {object_name} downloaded to {destination_path}")
        except ClientError as e:
            print(f"Error downloading file: {e}")


s3_client = S3Client(
    access_key="EEFJDEUXC1CROO48RUGL",
    secret_key="bOWBlZckIVapgodQAZ4X9cMeAWwQ1i9nZ8rBVppE",
    endpoint_url="https://s3.twcstorage.ru",  # для Selectel испол pьзуйте https://s3.storage.selcloud.ru
    bucket_name="edb6a103-vsecrm",
)

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

def filter_upp(request, filter_upp):
    records = Record.objects.filter(employees_UPP=filter_upp, companys=request.user.companys, felial=request.user.felial)
    return render(request, "home.html", {"records": records})

def brak(request):
    records = Record.objects.filter(status="Брак")
    return render(request, "home.html", {"records": records})

def logout_user(request):
    logout(request)
    return redirect("home")



async def record(request, pk):
    # Асинхронное получение объектов из БД
    get_record = sync_to_async(Record.objects.get, thread_sensitive=True)
    record = await get_record(id=pk)

    filter_surcharge = sync_to_async(Surcharge.objects.filter, thread_sensitive=True)
    surcharge = await filter_surcharge(record_id=pk)

    # Асинхронная инициализация форм
    init_form = sync_to_async(lambda: StatusForm(request.POST or None, instance=record), thread_sensitive=True)
    form_status = await init_form()

    init_employees_KC = sync_to_async(lambda: Employees_KCForm(request.POST or None, instance=record), thread_sensitive=True)
    form_employees_KC = await init_employees_KC()

    init_employees_UPP = sync_to_async(lambda: Employees_UPPForm(request.POST or None, instance=record), thread_sensitive=True)
    form_employees_UPP = await init_employees_UPP()

    init_cost_form = sync_to_async(lambda: CostForm(request.POST or None, instance=record), thread_sensitive=True)
    cost_form = await init_cost_form()

    init_upload_form = sync_to_async(lambda: FileUploadForm(request.POST or None, request.FILES or None, use_required_attribute=False), thread_sensitive=True)
    upload_file_form = await init_upload_form()

    # Проверка статуса бронирования
    check_booking = sync_to_async(Booking.objects.filter(client_id=pk).exists, thread_sensitive=True)
    booking_exists = await check_booking()
    get_status_com = 0
    if booking_exists:
        get_booking = sync_to_async(Booking.objects.get, thread_sensitive=True)
        get_status_com = await get_booking(client_id=pk)
    form_employees_KC_valid = await sync_to_async(form_employees_KC.is_valid, thread_sensitive=True)()
    form_employees_UPP_valid = await sync_to_async(form_employees_UPP.is_valid, thread_sensitive=True)()
    cost_valid = await sync_to_async(cost_form.is_valid, thread_sensitive=True)()
    upload_valid = await sync_to_async(upload_file_form.is_valid, thread_sensitive=True)()
    # Обработка форм
    form_status_valid = await sync_to_async(form_status.is_valid, thread_sensitive=True)()
    if form_status_valid:
        save_form = sync_to_async(form_status.save, thread_sensitive=True)
        await save_form()
        add_message = sync_to_async(messages.success, thread_sensitive=True)
        await add_message(request, "Статус успешно обновлен")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com
                       })


    elif form_employees_KC_valid:
        save_form = sync_to_async(form_employees_KC.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "Оператор прикреплен")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com
                       })


    elif form_employees_UPP_valid:
        save_form = sync_to_async(form_employees_UPP.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "Юрист прикреплен")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com
                       })


    elif cost_valid:
        save_form = sync_to_async(cost_form.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "Цена указана")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com
                       })


    elif upload_valid:
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))

        # Асинхронное сохранение файла
        save_file = sync_to_async(fs.save, thread_sensitive=True)
        filename = await save_file(uploaded_file.name, uploaded_file)

        full_path = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)
        print(full_path)
        # Асинхронная загрузка в S3
        await s3_client.upload_file(full_path, file_name=filename)

        # Обновление записи
        record.doc = f'https://s3.twcstorage.ru/edb6a103-vsecrm/{uploaded_file.name}'
        save_record = sync_to_async(record.save, thread_sensitive=True)
        await save_record()

        delete_file = sync_to_async(fs.delete, thread_sensitive=True)
        await delete_file(filename)

        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com
                       })

    # Рендер страницы, если нет валидных форм
    return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                   "form_employees_UPP": form_employees_UPP, "cost": cost_form, "surcharge": surcharge,
                   'upload_file_form': upload_file_form, 'get_status_com':get_status_com
                   })

def delete_record(request, pk):
    if request.user.is_authenticated:
        del_record = Record.objects.get(id=pk)
        del_record.delete()
        messages.success(request, "Вы спешно удалил запись")
        return redirect("home")
    else:
        return redirect("home")


async def delete_doc(request, pk):
    get_record = sync_to_async(Record.objects.get)
    save_record = sync_to_async(lambda instance: instance.save())
    try:
        del_doc = await get_record(id=pk)
        # Если нужно удалить файл, используйте delete_file вместо uploa d_file
        await s3_client.delete_file(object_name=del_doc.doc.replace('https://s3.twcstorage.ru/edb6a103-vsecrm/', ''))  # Проверьте атрибут имени файла
        del_doc.doc = None
        await save_record(del_doc)
        # Асинхронная отправка сообщения
        sync_messages = sync_to_async(messages.success, thread_sensitive=True)
        await sync_messages(request, "Файл успешно удалён")
    except Record.DoesNotExist:
        sync_messages_error = sync_to_async(messages.error, thread_sensitive=True)
        await sync_messages_error(request, "Документ не найден")
    #  Асинхронный редирект
    sync_redirect = sync_to_async(redirect, thread_sensitive=True)
    return await sync_redirect("home")

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
        for key, value in data.items():
            if key == "Phone":
                phone = value
            elif key == "Name":
                name = value
            elif key == "Textarea":
                textarea = value

            elif key == "id_company":
                id_company = value
        led = Record(phone=phone, name=name,  description=textarea, where="Tilda", companys=id_company)
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
            Q(phone__icontains=query)|
            Q(description__icontains=query)
        )

@csrf_exempt
@require_POST
def get_time(request):
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