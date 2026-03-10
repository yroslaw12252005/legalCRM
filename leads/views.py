from django.shortcuts import redirect, render, get_object_or_404
import os
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django import template

from accounts.views import employees
from company.views import companys
from felial.views import felials

# from rest_framework import generics

from .models import Record, RecordDocument
from todolist.models import ToDoList
from django.db.models import Sum
from cost.models import Surcharge
from accounts.models import User
from smart_calendar.models import Booking, RepresentativeBooking, CallBooking
from company.models import Companys
from cost.models import Surcharge

from .forms import (
    AddRecordForm,
    StatusForm,
    Employees_KCForm,
    Employees_UPPForm,
    Employees_REPForm,
    CostForm,
    FileUploadForm,
    RecordEditForm,
    RecordCommentForm,
)

import asyncio
from contextlib import asynccontextmanager
from aiobotocore.session import get_session
from botocore.exceptions import ClientError, ParamValidationError
import os
import json
import datetime
import calendar
import uuid
from datetime import date, datetime, timedelta
from collections import defaultdict
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import hmac

from asgiref.sync import sync_to_async
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

import asyncio
from contextlib import asynccontextmanager

from aiobotocore.session import get_session
from botocore.exceptions import ClientError, ParamValidationError


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
                return True
        except ParamValidationError as e:
            print(f"S3 config validation error uploading file: {e}")
            return False
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return False

    async def delete_file(self, object_name: str):
        try:
            async with self.get_client() as client:
                await client.delete_object(Bucket=self.bucket_name, Key=object_name)
                print(f"File {object_name} deleted from {self.bucket_name}")
                return True
        except ParamValidationError as e:
            print(f"S3 config validation error deleting file: {e}")
            return False
        except ClientError as e:
            print(f"Error deleting file: {e}")
            return False

    async def get_file(self, object_name: str, destination_path: str):
        try:
            async with self.get_client() as client:
                response = await client.get_object(Bucket=self.bucket_name, Key=object_name)
                data = await response["Body"].read()
                with open(destination_path, "wb") as file:
                    file.write(data)
                print(f"File {object_name} downloaded to {destination_path}")
                return True
        except ParamValidationError as e:
            print(f"S3 config validation error downloading file: {e}")
            return False
        except ClientError as e:
            print(f"Error downloading file: {e}")
            return False


s3_client = S3Client(
   access_key="EEFJDEUXC1CROO48RUGL",
        secret_key="bOWBlZckIVapgodQAZ4X9cMeAWwQ1i9nZ8rBVppE",
        endpoint_url="https://s3.twcstorage.ru",
        bucket_name="e5ce452e-71ce-493b-ad29-ff9ea3f60cb4",
)


def _s3_public_base_url():
    return f"{s3_client.config['endpoint_url'].rstrip('/')}/{s3_client.bucket_name}"


def _is_s3_configured():
    return bool(
        s3_client.bucket_name
        and s3_client.config.get("aws_access_key_id")
        and s3_client.config.get("aws_secret_access_key")
        and s3_client.config.get("endpoint_url")
    )


DOCUMENT_ALLOWED_STATUSES = {
    "Менеджер",
    "Директор ЮПП",
    "Директор представителей",
    "Представитель",
    "Юрист пирвичник",
    "Администратор",
}


def _status_variants(value):
    variants = {value}
    try:
        variants.add(value.encode("utf-8").decode("cp1251"))
    except Exception:
        pass
    try:
        variants.add(value.encode("cp1251").decode("utf-8"))
    except Exception:
        pass
    return variants


DOCUMENT_ALLOWED_STATUS_VARIANTS = set()
for _status in DOCUMENT_ALLOWED_STATUSES:
    DOCUMENT_ALLOWED_STATUS_VARIANTS.update(_status_variants(_status))

ASSIGN_KC_ALLOWED_STATUSES = {"Директор КЦ", "Администратор"}
ASSIGN_UPP_ALLOWED_STATUSES = {"Директор ЮПП", "Администратор"}
ASSIGN_REP_ALLOWED_STATUSES = {"Директор представителей", "Администратор"}
EDIT_RECORD_ALLOWED_STATUSES = {"Директор ЮПП", "Директор КЦ", "Администратор", "Оператор"}

EDIT_RECORD_ALLOWED_STATUS_VARIANTS = set()
for _status in EDIT_RECORD_ALLOWED_STATUSES:
    EDIT_RECORD_ALLOWED_STATUS_VARIANTS.update(_status_variants(_status))


def can_manage_documents(user):
    return user.is_authenticated and user.status in DOCUMENT_ALLOWED_STATUS_VARIANTS


def _record_for_user_or_404(request, pk):
    return get_object_or_404(Record, id=pk, companys=request.user.companys)


async def can_manage_documents_async(request):
    return await sync_to_async(
        lambda: request.user.is_authenticated and request.user.status in DOCUMENT_ALLOWED_STATUS_VARIANTS,
        thread_sensitive=True,
    )()


def _can_assign_kc(user):
    return user.status in ASSIGN_KC_ALLOWED_STATUSES


def _can_assign_upp(user):
    return user.status in ASSIGN_UPP_ALLOWED_STATUSES


def _can_assign_rep(user):
    return user.status in ASSIGN_REP_ALLOWED_STATUSES


def _can_edit_record_main(user):
    return user.status in EDIT_RECORD_ALLOWED_STATUS_VARIANTS

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
                messages.warning(request, "Не правильный логин или пароль")
                return redirect("home")
        else:
            return render(request, "home.html")
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    now = f"{year}-{month}-{day}"
    todolist = ToDoList.objects.all()
    if request.user.status == "Директор КЦ" or request.user.status == "Оператор":
        get_records = Record.objects.filter(companys=request.user.companys)
    else:
        get_records = Record.objects.filter(companys=request.user.companys, felial=request.user.felial)
    user = User.objects.filter(companys=request.user.companys)
    return render(request, "home.html", {"records": get_records, 'users':user, 'todolist':todolist, "now":now})

def filter(request, status):
    records = Record.objects.filter(status=status, companys=request.user.companys, felial=request.user.felial)
    return render(request, "home.html", {"records": records})

def filter_upp(request, filter_upp):
    records = Record.objects.filter(employees_UPP=filter_upp, companys=request.user.companys, felial=request.user.felial)
    return render(request, "home.html", {"records": records})

def filter_type(request, type):
    records = Record.objects.filter(type=type, companys=request.user.companys, felial=request.user.felial)
    return render(request, "home.html", {"records": records})

def brak(request):
    records = Record.objects.filter(status="Брак", companys=request.user.companys)
    return render(request, "home.html", {"records": records})

def logout_user(request):
    logout(request)
    return redirect("desktop")

@login_required
async def record(request, pk):
    current_user = await sync_to_async(lambda: request.user, thread_sensitive=True)()
    # Асинхронное получение объектов из БД
    get_record = sync_to_async(_record_for_user_or_404, thread_sensitive=True)
    record = await get_record(request, pk)
    request.can_manage_documents = await can_manage_documents_async(request)

    filter_surcharge = sync_to_async(Surcharge.objects.filter, thread_sensitive=True)
    surcharge = await filter_surcharge(record_id=pk)
    get_documents = sync_to_async(lambda: list(RecordDocument.objects.filter(record=record)), thread_sensitive=True)
    documents = await get_documents()

    # Асинхронная инициализация форм
    init_form = sync_to_async(lambda: StatusForm(request.POST or None, instance=record), thread_sensitive=True)
    form_status = await init_form()

    init_employees_KC = sync_to_async(
        lambda: Employees_KCForm(
            request.POST or None,
            instance=record,
            user=current_user,
            company_id=record.companys_id,
        ),
        thread_sensitive=True,
    )
    form_employees_KC = await init_employees_KC()

    init_employees_UPP = sync_to_async(
        lambda: Employees_UPPForm(
            request.POST or None,
            instance=record,
            user=current_user,
            company_id=record.companys_id,
        ),
        thread_sensitive=True,
    )
    form_employees_UPP = await init_employees_UPP()

    init_employees_REP = sync_to_async(
        lambda: Employees_REPForm(
            request.POST or None,
            instance=record,
            user=current_user,
            company_id=record.companys_id,
        ),
        thread_sensitive=True,
    )
    form_employees_REP = await init_employees_REP()

    init_cost_form = sync_to_async(lambda: CostForm(request.POST or None, instance=record), thread_sensitive=True)
    cost_form = await init_cost_form()

    init_upload_form = sync_to_async(lambda: FileUploadForm(request.POST or None, request.FILES or None, use_required_attribute=False), thread_sensitive=True)
    upload_file_form = await init_upload_form()

    # Удаляю инициализацию TopicForm

    # Проверка статуса бронирования
    check_booking = sync_to_async(
        Booking.objects.filter(client_id=pk, companys_id=record.companys_id).exists,
        thread_sensitive=True,
    )
    booking_exists = await check_booking()
    get_status_com = 0
    if booking_exists:
        get_booking = sync_to_async(Booking.objects.get, thread_sensitive=True)
        get_status_com = await get_booking(client_id=pk, companys_id=record.companys_id)
    form_employees_KC_valid = await sync_to_async(form_employees_KC.is_valid, thread_sensitive=True)()
    form_employees_UPP_valid = await sync_to_async(form_employees_UPP.is_valid, thread_sensitive=True)()
    form_employees_REP_valid = await sync_to_async(form_employees_REP.is_valid, thread_sensitive=True)()
    cost_valid = await sync_to_async(cost_form.is_valid, thread_sensitive=True)()
    upload_valid = request.can_manage_documents and await sync_to_async(upload_file_form.is_valid, thread_sensitive=True)()
    # Удаляю topic_form_valid
    # Обработка форм
    form_status_valid = await sync_to_async(form_status.is_valid, thread_sensitive=True)()
    if form_status_valid:
        save_form = sync_to_async(form_status.save, thread_sensitive=True)
        await save_form()
        add_message = sync_to_async(messages.success, thread_sensitive=True)
        await add_message(request, "Статус успешно обновлен")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })


    elif form_employees_KC_valid:
        if not _can_assign_kc(current_user):
            await sync_to_async(messages.warning)(request, "Недостаточно прав для прикрепления оператора")
            return await sync_to_async(redirect)("record", pk=pk)
        save_form = sync_to_async(form_employees_KC.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "Оператор прикреплен")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })


    elif form_employees_UPP_valid:
        if not _can_assign_upp(current_user):
            await sync_to_async(messages.warning)(request, "Недостаточно прав для прикрепления юриста")
            return await sync_to_async(redirect)("record", pk=pk)
        save_form = sync_to_async(form_employees_UPP.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "Юрист прикреплен")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })

    elif form_employees_REP_valid:
        if not _can_assign_rep(current_user):
            await sync_to_async(messages.warning)(request, "Недостаточно прав для прикрепления представителя")
            return await sync_to_async(redirect)("record", pk=pk)
        save_form = sync_to_async(form_employees_REP.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "Представитель прикреплен")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })


    elif cost_valid:
        save_form = sync_to_async(cost_form.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "Цена указана")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })


    elif upload_valid:
        if not _is_s3_configured():
            await sync_to_async(messages.error, thread_sensitive=True)(
                request,
                "S3 не настроен: проверьте S3_BUCKET_NAME, S3_ACCESS_KEY, S3_SECRET_KEY и S3_ENDPOINT_URL в settings.py",
            )
            return await sync_to_async(redirect, thread_sensitive=True)("record", pk=pk)

        uploaded_files = request.FILES.getlist('file')
        created_docs = 0
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
        save_file = sync_to_async(fs.save, thread_sensitive=True)
        delete_file = sync_to_async(fs.delete, thread_sensitive=True)
        create_doc = sync_to_async(RecordDocument.objects.create, thread_sensitive=True)

        for uploaded_file in uploaded_files:
            filename = await save_file(uploaded_file.name, uploaded_file)
            full_path = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)
            object_key = f"{record.companys_id}/{record.id}/{uuid.uuid4().hex}_{uploaded_file.name}"

            uploaded = await s3_client.upload_file(full_path, file_name=object_key)
            if not uploaded:
                await delete_file(filename)
                await sync_to_async(messages.error, thread_sensitive=True)(
                    request,
                    "Ошибка загрузки файла в S3. Проверьте настройки хранилища.",
                )
                return await sync_to_async(redirect, thread_sensitive=True)("record", pk=pk)
            safe_object_key = quote(object_key, safe="/")
            await create_doc(
                record=record,
                file_name=uploaded_file.name,
                file_url=f'{_s3_public_base_url()}/{safe_object_key}',
                s3_key=object_key,
            )
            await delete_file(filename)
            created_docs += 1

        if created_docs:
            await sync_to_async(messages.success)(request, f"Файлов загружено: {created_docs}")
        documents = await get_documents()

        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })

    # Удаляю topic_form из контекста рендера
    # Рендер страницы, если нет валидных форм
    return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                   "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                   'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                   })

@login_required
def delete_record(request, pk):
    del_record = _record_for_user_or_404(request, pk)
    del_record.delete()
    messages.success(request, "Вы спешно удалил запись")
    return redirect("home")


async def delete_doc(request, pk):
    can_manage_docs = await can_manage_documents_async(request)
    if not can_manage_docs:
        await sync_to_async(messages.warning, thread_sensitive=True)(request, "Нет прав для удаления документа")
        return await sync_to_async(redirect, thread_sensitive=True)("home")

    get_document = sync_to_async(RecordDocument.objects.select_related("record").get)
    delete_document = sync_to_async(lambda instance: instance.delete())
    get_user_company_id = sync_to_async(lambda: request.user.companys_id, thread_sensitive=True)
    try:
        del_doc = await get_document(id=pk)
        user_company_id = await get_user_company_id()
        if user_company_id != del_doc.record.companys_id:
            await sync_to_async(messages.warning, thread_sensitive=True)(request, "Нет доступа к документу")
            return await sync_to_async(redirect, thread_sensitive=True)("home")

        if del_doc.s3_key:
            await s3_client.delete_file(object_name=del_doc.s3_key)
        await delete_document(del_doc)

        sync_messages = sync_to_async(messages.success, thread_sensitive=True)
        await sync_messages(request, "Файл успешно удалён")
        return await sync_to_async(redirect, thread_sensitive=True)("record", pk=del_doc.record_id)
    except RecordDocument.DoesNotExist:
        sync_messages_error = sync_to_async(messages.error, thread_sensitive=True)
        await sync_messages_error(request, "Документ не найден")
        return await sync_to_async(redirect, thread_sensitive=True)("home")

@login_required
def add_record(request):
    form = AddRecordForm(request.POST or None, user=request.user)
    if form.is_valid():
        add_record = form.save(commit=False)
        add_record.companys = request.user.companys
        if request.user.status in _status_variants("Директор ЮПП"):
            add_record.in_work = True
            add_record.felial = request.user.felial
        if request.user.status =="Оператор":
            add_record.employees_KC = request.user.username
         # Прикрепляется к крмпании
        add_record.save()
        messages.success(request, f"Создана новая заявка {add_record.name}")
        return redirect("home")
    return render(request, "add_record.html", {"form": form})


@login_required
def update_record(request, pk):
    record = _record_for_user_or_404(request, pk)
    can_edit_main = _can_edit_record_main(request.user)
    edit_form = RecordEditForm(request.POST or None, instance=record)
    comment_form = RecordCommentForm(request.POST or None, instance=record)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_record":
            if not can_edit_main:
                messages.warning(request, "Нет прав для редактирования имени и описания")
                return redirect("update_record", pk=pk)
            if edit_form.is_valid():
                updated_record = edit_form.save()
                messages.success(request, f"Заявка '{updated_record.name}' обновлена")
                return redirect("record", pk=pk)
        elif action == "update_comment":
            if comment_form.is_valid():
                comment_form.save()
                messages.success(request, "Комментарий по ведению заявки обновлен")
                return redirect("record", pk=pk)

    return render(
        request,
        "update_record.html",
        {"edit_form": edit_form, "comment_form": comment_form, "can_edit_main": can_edit_main, "record": record},
    )

@login_required
def in_work(request, pk):
    record = _record_for_user_or_404(request, pk)
    record.in_work = 1
    record.save()
    return redirect("record", pk=pk)

@login_required
def to_representative(request, pk):
    if request.user.status not in ["Директор ЮПП", "Юрист пирвичник", "Администратор"]:
        messages.warning(request, "Нет прав для передачи в представителей")
        return redirect("record", pk=pk)
    record = _record_for_user_or_404(request, pk)
    record.representative = 1
    record.save()
    messages.success(request, "Заявка передана представителям")
    return redirect("record", pk=pk)


def download_document(request, doc_id):
    if not request.user.is_authenticated:
        return redirect("home")
    if not can_manage_documents(request.user):
        messages.warning(request, "Нет прав для скачивания документа")
        return redirect("home")

    try:
        document = RecordDocument.objects.select_related("record").get(id=doc_id)
    except RecordDocument.DoesNotExist:
        raise Http404("Документ не найден")

    if request.user.companys_id != document.record.companys_id:
        messages.warning(request, "Нет доступа к документу")
        return redirect("home")

    if document.s3_key:
        source_url = f"{_s3_public_base_url()}/{quote(document.s3_key, safe='/')}"
    else:
        parsed = urlsplit(document.file_url)
        source_url = urlunsplit((
            parsed.scheme,
            parsed.netloc,
            quote(parsed.path, safe="/"),
            parsed.query,
            parsed.fragment,
        ))

    filename = document.file_name or "document"
    
    with urlopen(source_url) as remote_file:
        content = remote_file.read()
   
        #Wmessages.error(request, "Не удалось скачать документ")
        #Wreturn redirect("record", pk=document.record_id)

    encoded_filename = quote(filename)
    response = HttpResponse(content, content_type="application/octet-stream")
    response["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
    response["X-Content-Type-Options"] = "nosniff"
    return response

#@csrf_exempt
#@require_POST
#def get_tilda_lead(request):
#    if request.POST.get('test', False):
#        print(200)
#        return HttpResponse("test")
#    else:
#        data = request.POST
#        phone = None
#        name = None
#        textarea = None
#        for key, value in data.items():
#            if key == "Phone":
#                phone = value
#            elif key == "Name":
#                name = value
#            elif key == "Textarea":
#                textarea = value
#
#            elif key == "id_company":
#                id_company = int(value)
#                get_company = Companys.objects.get(id=id_company)
#        led = Record(phone=phone, name=name,  description=textarea, where="Tilda", companys=get_company)
#        led.save()
#        print(200)
#        return HttpResponse(200)
@csrf_exempt
@require_POST
def get_tilda_lead(request):
    webhook_token = os.getenv("TILDA_WEBHOOK_TOKEN", "")
    if webhook_token:
        supplied_token = request.headers.get("X-Tilda-Token", "") or request.POST.get("token", "")
        if not hmac.compare_digest(supplied_token, webhook_token):
            return HttpResponse("Forbidden", status=403)

    if request.POST.get('test', False):
        print(200)
        return HttpResponse("test")
    else:
        data = request.POST
        phone = None
        name = None
        textarea = None
        get_company = None
        
        # Универсальная обработка полей
        for key, value in data.items():
            if key == "id_company":
                try:
                    id_company = int(value)
                except (TypeError, ValueError):
                    return HttpResponse("Invalid company id", status=400)
                get_company = Companys.objects.filter(id=id_company).first()
                continue
            
            # Пропускаем служебные поля
            if key in ['test', 'csrfmiddlewaretoken']:
                continue
                
            # Определяем тип поля по содержимому и ключу
            if not value or value.strip() == '':
                continue
                
            # Определение телефона
            if is_phone_field(key, value):
                phone = value
            # Определение имени
            elif is_name_field(key, value):
                name = value
            # Определение текстового поля (описание)
            elif is_text_field(key, value):
                textarea = value
        
        # Создаем запись только если есть хотя бы телефон или имя
        if (phone or name) and get_company is not None:
            led = Record(
                phone=phone, 
                name=name,  
                description=textarea, 
                where="Tilda", 
                companys=get_company
            )
            led.save()
            print(200)
            return HttpResponse(200)
        else:
            print("No valid data received")
            return HttpResponse("No valid data", status=400)

def is_phone_field(key, value):
    """Определяет, является ли поле телефоном"""
    # Проверяем по ключу
    phone_keywords = ['phone', 'tel', 'телефон', 'номер', 'number']
    if any(keyword in key.lower() for keyword in phone_keywords):
        return True
    
    # Проверяем по содержимому (содержит только цифры, +, -, (, ), пробелы)
    import re
    phone_pattern = r'^[\+]?[0-9\s\-\(\)]+$'
    if re.match(phone_pattern, value.strip()) and len(value.strip()) >= 7:
        return True
    
    return False

def is_name_field(key, value):
    """Определяет, является ли поле именем"""
    # Проверяем по ключу
    name_keywords = ['name', 'имя', 'fio', 'фио', 'contact', 'контакт']
    if any(keyword in key.lower() for keyword in name_keywords):
        return True
    
    # Проверяем по содержимому (содержит буквы, не слишком длинное)
    import re
    if re.match(r'^[а-яё\s\-]+$', value.strip(), re.IGNORECASE) or \
       re.match(r'^[a-z\s\-]+$', value.strip(), re.IGNORECASE):
        if 2 <= len(value.strip()) <= 50:
            return True
    
    return False

def is_text_field(key, value):
    """Определяет, является ли поле текстовым описанием"""
    # Проверяем по ключу
    text_keywords = ['text', 'message', 'comment', 'textarea', 'описание', 'сообщение', 'комментарий']
    if any(keyword in key.lower() for keyword in text_keywords):
        return True
    
    # Если поле длинное и не подходит под телефон/имя
    if len(value.strip()) > 20:
        return True
    
    return False
class SearchView(ListView):
    model = Record
    template_name = 'search_results.html'

    def get_queryset(self):
        query = (self.request.GET.get('q') or '').strip()
        if not query or not self.request.user.is_authenticated:
            return Record.objects.none()
        return Record.objects.filter(companys=self.request.user.companys).filter(
            Q(name__icontains=query) |  # Поиск по части имени
            Q(phone__icontains=query)|
            Q(id__icontains=query)|
            Q(description__icontains=query)
        )

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])  # Изменить это
def get_time(request):
    def _status_matches(value, *targets):
        if not value:
            return False
        variants = {value}
        try:
            variants.add(value.encode("utf-8").decode("cp1251"))
        except Exception:
            pass
        try:
            variants.add(value.encode("cp1251").decode("utf-8"))
        except Exception:
            pass
        return any(target in variants for target in targets)

    if request.method == "OPTIONS":
        response = HttpResponse()
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)
    
    if request.method == "POST":
        employee_id = request.user.id
        employee_status = request.user.status

        if _status_matches(employee_status, "ОП"):
            return HttpResponse("")

        selected_date = date.today()
        posted_date = request.POST.get("date")
        if posted_date:
            try:
                selected_date = datetime.strptime(posted_date, "%Y-%m-%d").date()
            except ValueError:
                pass

        year, month = selected_date.year, selected_date.month
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)
        start_date = date(year, month, 1)
        end_date = (start_date + timedelta(days=31)).replace(day=1)

        is_rep_director = _status_matches(employee_status, "Директор представителей")
        is_representative = _status_matches(employee_status, "Представитель")

        if is_rep_director or is_representative:
            base_bookings = RepresentativeBooking.objects.filter(
                date__gte=start_date,
                date__lt=end_date,
                companys=request.user.companys,
            )
            if is_representative:
                bookings = base_bookings.filter(representative=employee_id)
            else:
                bookings = base_bookings
            day_link_name = "representative_calendar"
        else:
            base_bookings = Booking.objects.filter(
                date__gte=start_date,
                date__lt=end_date,
                companys=request.user.companys,
                felial=request.user.felial,
                client__status="Запись в офис",
            )
            base_call_bookings = CallBooking.objects.filter(
                date__gte=start_date,
                date__lt=end_date,
                companys=request.user.companys,
                felial=request.user.felial,
            )

            is_management = _status_matches(
                employee_status,
                "Менеджер",
                "Администратор",
                "Директор ЮПП",
                "Директор КЦ",
            )
            is_lawyer = _status_matches(employee_status, "Юрист пирвичник")

            if is_management:
                bookings = base_bookings
                call_bookings = base_call_bookings
            elif is_lawyer:
                bookings = base_bookings.filter(employees=employee_id)
                call_bookings = base_call_bookings.filter(employees=employee_id)
            else:
                bookings = base_bookings.filter(registrar=employee_id)
                call_bookings = base_call_bookings.filter(registrar=employee_id)
            day_link_name = "calendar"

        bookings_per_day = defaultdict(int)
        for booking in bookings:
            current_day = booking.date
            if current_day and start_date <= current_day < end_date:
                bookings_per_day[current_day.day] += 1
        if day_link_name == "calendar":
            for call_booking in call_bookings:
                current_day = call_booking.date
                if current_day and start_date <= current_day < end_date:
                    bookings_per_day[current_day.day] += 1

        today_date = date.today()
        formatted_weeks = []
        for week in month_days:
            formatted_week = []
            for day in week:
                is_today = day != 0 and today_date.year == year and today_date.month == month and today_date.day == day
                formatted_week.append(
                    {
                        "day": day,
                        "year": year,
                        "month": month,
                        "count": bookings_per_day.get(day, 0),
                        "surcharges_count": 0,
                        "is_today": is_today,
                    }
                )
            formatted_weeks.append(formatted_week)

        ru_months = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
        ]
        return render(
            request,
            "mini_calendar.html",
            {
                "month_name": f"{ru_months[month - 1]} {year}",
                "header": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
                "weeks": formatted_weeks,
                "today": today_date.day,
                "day_link_name": day_link_name,
            },
        )
    
    return HttpResponse("Метод не разрешён", status=405)
