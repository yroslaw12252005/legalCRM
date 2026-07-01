from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render

from leads.access import status_matches

from .models import CallRecording


ALLOWED_STATUSES = ("Директор КЦ", "Директор ЮПП", "Администратор")


def can_view_recordings(user):
    return user.is_authenticated and status_matches(user.status, *ALLOWED_STATUSES)


def build_safe_url(url):
    parsed = urlsplit(url)
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            quote(parsed.path, safe="/"),
            parsed.query,
            parsed.fragment,
        )
    )


def build_recording_source_url(recording):
    safe_file_url = build_safe_url(recording.file_url)
    if not recording.s3_key:
        return safe_file_url

    parsed = urlsplit(recording.file_url)
    quoted_s3_key = quote(recording.s3_key, safe="/")

    # For old rows, file_url can already point to the real object while s3_key no longer matches it.
    if parsed.path.endswith(quoted_s3_key):
        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                f"/{quoted_s3_key}",
                parsed.query,
                parsed.fragment,
            )
        )

    return safe_file_url


def build_recording_download_urls(recording):
    urls = []

    if recording.s3_key:
        base_url = f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET_NAME}"
        urls.append(f"{base_url}/{quote(recording.s3_key, safe='/')}")

    safe_file_url = build_safe_url(recording.file_url)
    if safe_file_url and safe_file_url not in urls:
        urls.append(safe_file_url)

    return urls


@login_required
def get_calls(request):
    if not can_view_recordings(request.user):
        messages.warning(request, "У вас нет доступа к записям разговоров.")
        return redirect("current_applications")

    query = (request.GET.get("phone") or "").strip()
    recordings = CallRecording.objects.filter(companys=request.user.companys)
    if query:
        recordings = recordings.filter(Q(phone__icontains=query) | Q(operator_phone__icontains=query))

    return render(
        request,
        "call_recording.html",
        {
            "recordings": recordings.order_by("-call_started_at", "-created_at"),
            "query": query,
        },
    )


@login_required
def download_call(request, pk):
    if not can_view_recordings(request.user):
        messages.warning(request, "У вас нет доступа к записям разговоров.")
        return redirect("current_applications")

    try:
        recording = CallRecording.objects.get(id=pk, companys=request.user.companys)
    except CallRecording.DoesNotExist:
        raise Http404("Запись разговора не найдена")

    filename = recording.file_name or "call-recording.mp3"
    content = None

    for source_url in build_recording_download_urls(recording):
        try:
            with urlopen(source_url) as remote_file:
                content = remote_file.read()
            break
        except (HTTPError, URLError, OSError):
            continue

    if content is None:
        raise Http404("Не удалось скачать запись разговора")

    encoded_filename = quote(filename)
    response = HttpResponse(content, content_type="application/octet-stream")
    response["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
    response["X-Content-Type-Options"] = "nosniff"
    return response
