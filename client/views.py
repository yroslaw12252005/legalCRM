from django.contrib.auth.decorators import login_required
from urllib.error import URLError

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from leads.document_download import build_document_download_response
from leads.models import Record, RecordDocument


def _client_cabinet_records():
    return Record.objects.prefetch_related("contracts__surcharges", "documents")


def _render_client_cabinet(request, record):
    response = render(
        request,
        "client_inform.html",
        {
            "info": record,
            "contracts": record.contracts.all(),
            "documents": record.documents.all(),
        },
    )
    response["Cache-Control"] = "private, no-store"
    response["Pragma"] = "no-cache"
    response["Referrer-Policy"] = "no-referrer"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@login_required
def client_informs(request, pk):
    get_record_info = get_object_or_404(
        _client_cabinet_records(),
        id=pk,
        companys=request.user.companys,
    )
    return _render_client_cabinet(request, get_record_info)


def client_portal(request, token):
    record = get_object_or_404(
        _client_cabinet_records(),
        client_access_token=token,
    )
    return _render_client_cabinet(request, record)


def client_document_download(request, token, doc_id):
    document = get_object_or_404(
        RecordDocument.objects.select_related("record"),
        id=doc_id,
        record__client_access_token=token,
    )
    try:
        return build_document_download_response(document)
    except (OSError, URLError):
        return HttpResponse("Не удалось скачать документ", status=502)
