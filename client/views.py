import uuid
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote

from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import User
from leads.document_download import build_document_download_response
from leads.document_storage import document_storage, document_storage_is_configured
from leads.models import Record, RecordDocument

from .forms import ClientDocumentUploadForm


PAYMENT_URL = "https://paylink.tbank.ru/6c2772a4-247c-40a7-9a9f-bc30990d346b"


def _initials(value, fallback="КЛ"):
    parts = [part for part in (value or "").split() if part]
    return "".join(part[0] for part in parts[:2]).upper() or fallback


def _client_cabinet_records():
    return Record.objects.prefetch_related("contracts__surcharges", "documents")


def _render_client_cabinet(request, record):
    contracts = list(record.contracts.all())
    documents = list(record.documents.all())
    lawyer = None
    if record.employees_UPP and record.employees_UPP != "Не прикреплён":
        lawyer = User.objects.filter(
            companys_id=record.companys_id,
            username=record.employees_UPP,
        ).first()

    lawyer_name = "Юрист ещё не назначен"
    lawyer_email = ""
    if lawyer:
        lawyer_name = lawyer.get_full_name().strip() or lawyer.username
        lawyer_email = lawyer.email or ""
    elif record.employees_UPP and record.employees_UPP != "Не прикреплён":
        lawyer_name = record.employees_UPP

    response = render(
        request,
        "client_inform.html",
        {
            "info": record,
            "contracts": contracts,
            "documents": documents,
            "document_count": len(documents) + int(bool(record.doc)),
            "client_initials": _initials(record.name),
            "lawyer_name": lawyer_name,
            "lawyer_initials": _initials(lawyer_name, fallback="ЮР"),
            "lawyer_email": lawyer_email,
            "payment_url": getattr(settings, "CLIENT_PAYMENT_URL", PAYMENT_URL),
            "upload_form": ClientDocumentUploadForm(),
        },
    )
    response["Cache-Control"] = "private, no-store"
    response["Pragma"] = "no-cache"
    response["Referrer-Policy"] = "no-referrer"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@login_required
def client_informs(request, pk):
    record = get_object_or_404(
        _client_cabinet_records(),
        id=pk,
        companys=request.user.companys,
    )
    return _render_client_cabinet(request, record)


def client_portal(request, token):
    record = get_object_or_404(
        _client_cabinet_records(),
        client_access_token=token,
    )
    return _render_client_cabinet(request, record)


@require_POST
def client_document_upload(request, token):
    record = get_object_or_404(Record, client_access_token=token)
    form = ClientDocumentUploadForm(request.POST, request.FILES)

    if not form.is_valid():
        error = next(iter(form.errors.values()))[0]
        messages.error(request, error)
        return redirect(f"{reverse('client_portal', args=[token])}#documents")

    if not document_storage_is_configured():
        messages.error(request, "Хранилище документов временно недоступно")
        return redirect(f"{reverse('client_portal', args=[token])}#documents")

    uploaded_file = form.cleaned_data["file"]
    file_name = Path(uploaded_file.name).name
    object_key = (
        f"{record.companys_id}/{record.id}/client/"
        f"{uuid.uuid4().hex}_{file_name}"
    )
    uploaded = async_to_sync(document_storage.upload_bytes)(
        uploaded_file.read(),
        object_key,
        getattr(uploaded_file, "content_type", None),
    )
    if not uploaded:
        messages.error(request, "Не удалось загрузить файл. Попробуйте ещё раз")
        return redirect(f"{reverse('client_portal', args=[token])}#documents")

    base_url = f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET_NAME}"
    RecordDocument.objects.create(
        record=record,
        file_name=file_name,
        file_url=f"{base_url}/{quote(object_key, safe='/')}",
        s3_key=object_key,
    )
    messages.success(request, "Документ успешно загружен")
    return redirect(f"{reverse('client_portal', args=[token])}#documents")


def client_document_download(request, token, doc_id):
    document = get_object_or_404(
        RecordDocument.objects.select_related("record"),
        id=doc_id,
        record__client_access_token=token,
    )
    try:
        return build_document_download_response(document)
    except (OSError, URLError, ValueError):
        return HttpResponse("Не удалось скачать документ", status=502)
