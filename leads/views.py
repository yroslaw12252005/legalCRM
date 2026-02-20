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
from smart_calendar.models import Booking
from company.models import Companys
from cost.models import Surcharge

from .forms import AddRecordForm, StatusForm, Employees_KCForm, Employees_UPPForm, Employees_REPForm, CostForm,FileUploadForm

import asyncio
from contextlib import asynccontextmanager
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
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
    access_key=os.getenv("S3_ACCESS_KEY", ""),
    secret_key=os.getenv("S3_SECRET_KEY", ""),
    endpoint_url=os.getenv("S3_ENDPOINT_URL", "https://s3.twcstorage.ru"),  # РґР»СЏ Selectel РёСЃРїРѕР»СЊР·СѓР№С‚Рµ https://s3.storage.selcloud.ru
    bucket_name=os.getenv("S3_BUCKET_NAME", ""),
)


def _s3_public_base_url():
    return f"{s3_client.config['endpoint_url'].rstrip('/')}/{s3_client.bucket_name}"


DOCUMENT_ALLOWED_STATUSES = {
    "РњРµРЅРµРґР¶РµСЂ",
    "Р”РёСЂРµРєС‚РѕСЂ Р®РџРџ",
    "Р”РёСЂРµРєС‚РѕСЂ РїСЂРµРґСЃС‚Р°РІРёС‚РµР»РµР№",
    "РџСЂРµРґСЃС‚Р°РІРёС‚РµР»СЊ",
    "Р®СЂРёСЃС‚ РїРёСЂРІРёС‡РЅРёРє",
    "РђРґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂ",
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


def can_manage_documents(user):
    return user.is_authenticated and user.status in DOCUMENT_ALLOWED_STATUS_VARIANTS


def _record_for_user_or_404(request, pk):
    return get_object_or_404(Record, id=pk, companys=request.user.companys)


async def can_manage_documents_async(request):
    return await sync_to_async(
        lambda: request.user.is_authenticated and request.user.status in DOCUMENT_ALLOWED_STATUS_VARIANTS,
        thread_sensitive=True,
    )()

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
                messages.warning(request, "РќРµ РїСЂР°РІРёР»СЊРЅС‹Р№ Р»РѕРіРёРЅ РёР»Рё РїР°СЂРѕР»СЊ")
                return redirect("home")
        else:
            return render(request, "home.html")
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    now = f"{year}-{month}-{day}"
    todolist = ToDoList.objects.all()
    if request.user.status == "Р”РёСЂРµРєС‚РѕСЂ РљР¦" or request.user.status == "РћРїРµСЂР°С‚РѕСЂ":
        get_records = Record.objects.filter(companys=request.user.companys)
    else:
        get_records = Record.objects.filter(companys=request.user.companys, felial=request.user.felial)
    user  =  User.objects.all()
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
    records = Record.objects.filter(status="Р‘СЂР°Рє")
    return render(request, "home.html", {"records": records})

def logout_user(request):
    logout(request)
    return redirect("desktop")



async def record(request, pk):
    # РђСЃРёРЅС…СЂРѕРЅРЅРѕРµ РїРѕР»СѓС‡РµРЅРёРµ РѕР±СЉРµРєС‚РѕРІ РёР· Р‘Р”
    get_record = sync_to_async(Record.objects.get, thread_sensitive=True)
    record = await get_record(id=pk)
    request.can_manage_documents = await can_manage_documents_async(request)

    filter_surcharge = sync_to_async(Surcharge.objects.filter, thread_sensitive=True)
    surcharge = await filter_surcharge(record_id=pk)
    get_documents = sync_to_async(lambda: list(RecordDocument.objects.filter(record_id=pk)), thread_sensitive=True)
    documents = await get_documents()

    # РђСЃРёРЅС…СЂРѕРЅРЅР°СЏ РёРЅРёС†РёР°Р»РёР·Р°С†РёСЏ С„РѕСЂРј
    init_form = sync_to_async(lambda: StatusForm(request.POST or None, instance=record), thread_sensitive=True)
    form_status = await init_form()

    init_employees_KC = sync_to_async(lambda: Employees_KCForm(request.POST or None, instance=record), thread_sensitive=True)
    form_employees_KC = await init_employees_KC()

    init_employees_UPP = sync_to_async(lambda: Employees_UPPForm(request.POST or None, instance=record), thread_sensitive=True)
    form_employees_UPP = await init_employees_UPP()

    init_employees_REP = sync_to_async(lambda: Employees_REPForm(request.POST or None, instance=record), thread_sensitive=True)
    form_employees_REP = await init_employees_REP()

    init_cost_form = sync_to_async(lambda: CostForm(request.POST or None, instance=record), thread_sensitive=True)
    cost_form = await init_cost_form()

    init_upload_form = sync_to_async(lambda: FileUploadForm(request.POST or None, request.FILES or None, use_required_attribute=False), thread_sensitive=True)
    upload_file_form = await init_upload_form()

    # РЈРґР°Р»СЏСЋ РёРЅРёС†РёР°Р»РёР·Р°С†РёСЋ TopicForm

    # РџСЂРѕРІРµСЂРєР° СЃС‚Р°С‚СѓСЃР° Р±СЂРѕРЅРёСЂРѕРІР°РЅРёСЏ
    check_booking = sync_to_async(Booking.objects.filter(client_id=pk).exists, thread_sensitive=True)
    booking_exists = await check_booking()
    get_status_com = 0
    if booking_exists:
        get_booking = sync_to_async(Booking.objects.get, thread_sensitive=True)
        get_status_com = await get_booking(client_id=pk)
    form_employees_KC_valid = await sync_to_async(form_employees_KC.is_valid, thread_sensitive=True)()
    form_employees_UPP_valid = await sync_to_async(form_employees_UPP.is_valid, thread_sensitive=True)()
    form_employees_REP_valid = await sync_to_async(form_employees_REP.is_valid, thread_sensitive=True)()
    cost_valid = await sync_to_async(cost_form.is_valid, thread_sensitive=True)()
    upload_valid = request.can_manage_documents and await sync_to_async(upload_file_form.is_valid, thread_sensitive=True)()
    # РЈРґР°Р»СЏСЋ topic_form_valid
    # РћР±СЂР°Р±РѕС‚РєР° С„РѕСЂРј
    form_status_valid = await sync_to_async(form_status.is_valid, thread_sensitive=True)()
    if form_status_valid:
        save_form = sync_to_async(form_status.save, thread_sensitive=True)
        await save_form()
        add_message = sync_to_async(messages.success, thread_sensitive=True)
        await add_message(request, "РЎС‚Р°С‚СѓСЃ СѓСЃРїРµС€РЅРѕ РѕР±РЅРѕРІР»РµРЅ")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })


    elif form_employees_KC_valid:
        save_form = sync_to_async(form_employees_KC.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "РћРїРµСЂР°С‚РѕСЂ РїСЂРёРєСЂРµРїР»РµРЅ")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })


    elif form_employees_UPP_valid:
        save_form = sync_to_async(form_employees_UPP.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "Р®СЂРёСЃС‚ РїСЂРёРєСЂРµРїР»РµРЅ")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })

    elif form_employees_REP_valid:
        save_form = sync_to_async(form_employees_REP.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "РџСЂРµРґСЃС‚Р°РІРёС‚РµР»СЊ РїСЂРёРєСЂРµРїР»РµРЅ")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })


    elif cost_valid:
        save_form = sync_to_async(cost_form.save, thread_sensitive=True)
        await save_form()
        await sync_to_async(messages.success)(request, "Р¦РµРЅР° СѓРєР°Р·Р°РЅР°")
        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })


    elif upload_valid:
        uploaded_files = request.FILES.getlist('file')
        created_docs = 0
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
        save_file = sync_to_async(fs.save, thread_sensitive=True)
        delete_file = sync_to_async(fs.delete, thread_sensitive=True)
        create_doc = sync_to_async(RecordDocument.objects.create, thread_sensitive=True)

        for uploaded_file in uploaded_files:
            filename = await save_file(uploaded_file.name, uploaded_file)
            full_path = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)
            object_key = f"records/{record.id}/{uuid.uuid4().hex}_{uploaded_file.name}"

            await s3_client.upload_file(full_path, file_name=object_key)
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
            await sync_to_async(messages.success)(request, f"Р¤Р°Р№Р»РѕРІ Р·Р°РіСЂСѓР¶РµРЅРѕ: {created_docs}")
        documents = await get_documents()

        return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                       "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                       'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                       })

    # РЈРґР°Р»СЏСЋ topic_form РёР· РєРѕРЅС‚РµРєСЃС‚Р° СЂРµРЅРґРµСЂР°
    # Р РµРЅРґРµСЂ СЃС‚СЂР°РЅРёС†С‹, РµСЃР»Рё РЅРµС‚ РІР°Р»РёРґРЅС‹С… С„РѕСЂРј
    return await sync_to_async(render)(request, "record.html", {"record": record, "form_status": form_status, "form_employees_KC": form_employees_KC,
                   "form_employees_UPP": form_employees_UPP, "form_employees_REP": form_employees_REP, "cost": cost_form, "surcharge": surcharge,
                   'upload_file_form': upload_file_form, 'get_status_com':get_status_com, "documents": documents, "can_manage_documents": request.can_manage_documents
                   })

@login_required
def delete_record(request, pk):
    del_record = _record_for_user_or_404(request, pk)
    del_record.delete()
    messages.success(request, "Р’С‹ СЃРїРµС€РЅРѕ СѓРґР°Р»РёР» Р·Р°РїРёСЃСЊ")
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
        if request.user.status =="РћРїРµСЂР°С‚РѕСЂ":
            add_record.employees_KC = request.user.username
         # РџСЂРёРєСЂРµРїР»СЏРµС‚СЃСЏ Рє РєСЂРјРїР°РЅРёРё
        add_record.save()
        messages.success(request, f"Р—Р°СЏРІРєР°  СЃ РёРјРµРЅРµРј {add_record.name} СѓСЃРїРµС€РЅРѕ СЃРѕР·РґР°РЅР°")
        return redirect("home")
    return render(request, "add_record.html", {"form": form})


@login_required
def update_record(request, pk):
    record = _record_for_user_or_404(request, pk)
    form = AddRecordForm(request.POST or None, instance=record,  user=request.user)
    if form.is_valid():
        updated_record = form.save()
        messages.success(request, f"Р—Р°РїРёСЃСЊ '{updated_record.name}' РѕР±РЅР°РІР»РµРЅР°")
        return redirect("record", pk=pk)
    return render(request, "update_record.html", {"form": form})

@login_required
def in_work(request, pk):
    record = _record_for_user_or_404(request, pk)
    record.in_work = 1
    record.save()
    return redirect("record", pk=pk)

@login_required
def to_representative(request, pk):
    if request.user.status not in ["Р”РёСЂРµРєС‚РѕСЂ Р®РџРџ", "Р®СЂРёСЃС‚ РїРёСЂРІРёС‡РЅРёРє", "РђРґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂ"]:
        messages.warning(request, "РќРµС‚ РїСЂР°РІ РґР»СЏ РїРµСЂРµРґР°С‡Рё РІ РїСЂРµРґСЃС‚Р°РІРёС‚РµР»РµР№")
        return redirect("record", pk=pk)
    record = _record_for_user_or_404(request, pk)
    record.representative = 1
    record.save()
    messages.success(request, "Р—Р°СЏРІРєР° РїРµСЂРµРґР°РЅР° РїСЂРµРґСЃС‚Р°РІРёС‚РµР»СЏРј")
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
        raise Http404("Р”РѕРєСѓРјРµРЅС‚ РЅРµ РЅР°Р№РґРµРЅ")

    if request.user.companys_id != document.record.companys_id:
        messages.warning(request, "РќРµС‚ РґРѕСЃС‚СѓРїР° Рє РґРѕРєСѓРјРµРЅС‚Сѓ")
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
   
        #Wmessages.error(request, "РќРµ СѓРґР°Р»РѕСЃСЊ СЃРєР°С‡Р°С‚СЊ РґРѕРєСѓРјРµРЅС‚")
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
        
        # РЈРЅРёРІРµСЂСЃР°Р»СЊРЅР°СЏ РѕР±СЂР°Р±РѕС‚РєР° РїРѕР»РµР№
        for key, value in data.items():
            if key == "id_company":
                try:
                    id_company = int(value)
                except (TypeError, ValueError):
                    return HttpResponse("Invalid company id", status=400)
                get_company = Companys.objects.filter(id=id_company).first()
                continue
            
            # РџСЂРѕРїСѓСЃРєР°РµРј СЃР»СѓР¶РµР±РЅС‹Рµ РїРѕР»СЏ
            if key in ['test', 'csrfmiddlewaretoken']:
                continue
                
            # РћРїСЂРµРґРµР»СЏРµРј С‚РёРї РїРѕР»СЏ РїРѕ СЃРѕРґРµСЂР¶РёРјРѕРјСѓ Рё РєР»СЋС‡Сѓ
            if not value or value.strip() == '':
                continue
                
            # РћРїСЂРµРґРµР»РµРЅРёРµ С‚РµР»РµС„РѕРЅР°
            if is_phone_field(key, value):
                phone = value
            # РћРїСЂРµРґРµР»РµРЅРёРµ РёРјРµРЅРё
            elif is_name_field(key, value):
                name = value
            # РћРїСЂРµРґРµР»РµРЅРёРµ С‚РµРєСЃС‚РѕРІРѕРіРѕ РїРѕР»СЏ (РѕРїРёСЃР°РЅРёРµ)
            elif is_text_field(key, value):
                textarea = value
        
        # РЎРѕР·РґР°РµРј Р·Р°РїРёСЃСЊ С‚РѕР»СЊРєРѕ РµСЃР»Рё РµСЃС‚СЊ С…РѕС‚СЏ Р±С‹ С‚РµР»РµС„РѕРЅ РёР»Рё РёРјСЏ
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
    """РћРїСЂРµРґРµР»СЏРµС‚, СЏРІР»СЏРµС‚СЃСЏ Р»Рё РїРѕР»Рµ С‚РµР»РµС„РѕРЅРѕРј"""
    # РџСЂРѕРІРµСЂСЏРµРј РїРѕ РєР»СЋС‡Сѓ
    phone_keywords = ['phone', 'tel', 'С‚РµР»РµС„РѕРЅ', 'РЅРѕРјРµСЂ', 'number']
    if any(keyword in key.lower() for keyword in phone_keywords):
        return True
    
    # РџСЂРѕРІРµСЂСЏРµРј РїРѕ СЃРѕРґРµСЂР¶РёРјРѕРјСѓ (СЃРѕРґРµСЂР¶РёС‚ С‚РѕР»СЊРєРѕ С†РёС„СЂС‹, +, -, (, ), РїСЂРѕР±РµР»С‹)
    import re
    phone_pattern = r'^[\+]?[0-9\s\-\(\)]+$'
    if re.match(phone_pattern, value.strip()) and len(value.strip()) >= 7:
        return True
    
    return False

def is_name_field(key, value):
    """РћРїСЂРµРґРµР»СЏРµС‚, СЏРІР»СЏРµС‚СЃСЏ Р»Рё РїРѕР»Рµ РёРјРµРЅРµРј"""
    # РџСЂРѕРІРµСЂСЏРµРј РїРѕ РєР»СЋС‡Сѓ
    name_keywords = ['name', 'РёРјСЏ', 'fio', 'С„РёРѕ', 'contact', 'РєРѕРЅС‚Р°РєС‚']
    if any(keyword in key.lower() for keyword in name_keywords):
        return True
    
    # РџСЂРѕРІРµСЂСЏРµРј РїРѕ СЃРѕРґРµСЂР¶РёРјРѕРјСѓ (СЃРѕРґРµСЂР¶РёС‚ Р±СѓРєРІС‹, РЅРµ СЃР»РёС€РєРѕРј РґР»РёРЅРЅРѕРµ)
    import re
    if re.match(r'^[Р°-СЏС‘\s\-]+$', value.strip(), re.IGNORECASE) or \
       re.match(r'^[a-z\s\-]+$', value.strip(), re.IGNORECASE):
        if 2 <= len(value.strip()) <= 50:
            return True
    
    return False

def is_text_field(key, value):
    """РћРїСЂРµРґРµР»СЏРµС‚, СЏРІР»СЏРµС‚СЃСЏ Р»Рё РїРѕР»Рµ С‚РµРєСЃС‚РѕРІС‹Рј РѕРїРёСЃР°РЅРёРµРј"""
    # РџСЂРѕРІРµСЂСЏРµРј РїРѕ РєР»СЋС‡Сѓ
    text_keywords = ['text', 'message', 'comment', 'textarea', 'РѕРїРёСЃР°РЅРёРµ', 'СЃРѕРѕР±С‰РµРЅРёРµ', 'РєРѕРјРјРµРЅС‚Р°СЂРёР№']
    if any(keyword in key.lower() for keyword in text_keywords):
        return True
    
    # Р•СЃР»Рё РїРѕР»Рµ РґР»РёРЅРЅРѕРµ Рё РЅРµ РїРѕРґС…РѕРґРёС‚ РїРѕРґ С‚РµР»РµС„РѕРЅ/РёРјСЏ
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
            Q(name__icontains=query) |  # РџРѕРёСЃРє РїРѕ С‡Р°СЃС‚Рё РёРјРµРЅРё
            Q(phone__icontains=query)|
            Q(id__icontains=query)|
            Q(description__icontains=query)
        )

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])  # РР·РјРµРЅРёС‚СЊ СЌС‚Рѕ
def get_time(request):
    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    if request.method == "OPTIONS":
        response = HttpResponse()
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if request.method == "POST":
        employee_id = request.user.id
        employee_status = request.user.status
        if employee_status == "РћРџ":
            response = HttpResponse("")
            return response
        today = date.today()
        if request.method == "POST":
           today = request.POST['date']
           today = datetime.strptime(today, '%Y-%m-%d')
        year, month = today.year, today.month
        cal = calendar.Calendar(firstweekday=7)
        month_days = cal.monthdayscalendar(year, month)

        # Р“СЂР°РЅРёС†С‹ РјРµСЃСЏС†Р°
        start_date = date(year, month, 1)
        end_date = (start_date + timedelta(days=31)).replace(day=1)
        if employee_status == "РњРµРЅРµРґР¶РµСЂ" or employee_status == "РђРґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂ" or employee_status == "Р”РёСЂРµРєС‚РѕСЂ Р®РџРџ" or employee_status == "Р”РёСЂРµРєС‚РѕСЂ РљР¦":
            # РџРѕР»СѓС‡РµРЅРёРµ РґР°РЅРЅС‹С…
            bookings = Booking.objects.filter(
                date__lt=end_date,
                date__gte=start_date
            )

            # РСЃРїСЂР°РІР»РµРЅРЅС‹Р№ С„РёР»СЊС‚СЂ РґР»СЏ РґРѕРїР»Р°С‚
            surcharges = Surcharge.objects.filter(dat__range=(start_date, end_date))
        else:
            if employee_status != "Р®СЂРёСЃС‚ РїРёСЂРІРёС‡РЅРёРє":
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

            # РСЃРїСЂР°РІР»РµРЅРЅС‹Р№ С„РёР»СЊС‚СЂ РґР»СЏ РґРѕРїР»Р°С‚
            surcharges = Surcharge.objects.filter(dat__range=(start_date, end_date), responsible=employee_id)

        # РџРѕРґСЃС‡РµС‚ РґРѕРїР»Р°С‚
        surcharges_per_day = defaultdict(int)
        for surcharge in surcharges:
            current_day = surcharge.dat.date()
            if start_date <= current_day < end_date:
                surcharges_per_day[current_day.day] += 1

        # РџРѕРґСЃС‡РµС‚ Р±СЂРѕРЅРёСЂРѕРІР°РЅРёР№
        bookings_per_day = defaultdict(int)
        for booking in bookings:
            current_day = booking.date
            if start_date <= current_day < end_date:
                bookings_per_day[current_day.day] += 1
            current_day += timedelta(days=1)

        # Р¤РѕСЂРјР°С‚РёСЂРѕРІР°РЅРёРµ РґР°РЅРЅС‹С…
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

        response = render(request, "mini_calendar.html", {
            'month_name': f"{calendar.month_name[month]} {year}",
            'header': ['Рџ', 'Р’', 'РЎ', 'Р§', 'Рџ', 'РЎ', 'Р’'],
            'weeks': formatted_weeks,
            'today': today.day
        })
        return response
    
    return HttpResponse("РњРµС‚РѕРґ РЅРµ СЂР°Р·СЂРµС€С‘РЅ", status=405)





