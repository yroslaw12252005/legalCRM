from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import urlopen

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


def build_s3_url(recording):
    parsed = urlsplit(recording.file_url)
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            f"/{quote(recording.s3_key, safe='/')}",
            parsed.query,
            parsed.fragment,
        )
    )


def read_remote_bytes(urls):
    last_error = None
    for url in urls:
        if not url:
            continue
        try:
            with urlopen(url) as remote_file:
                return remote_file.read()
        except (HTTPError, URLError) as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise Http404("Файл записи не найден")


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

    candidate_urls = [build_safe_url(recording.file_url)]
    if recording.s3_key:
        s3_url = build_s3_url(recording)
        if s3_url not in candidate_urls:
            candidate_urls.append(s3_url)

    try:
        content = read_remote_bytes(candidate_urls)
    except (HTTPError, URLError):
        messages.error(request, "Не удалось скачать запись разговора.")
        return redirect("get_calls")

    filename = recording.file_name or "call-recording.mp3"
    response = HttpResponse(content, content_type="audio/mpeg")
    response["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(filename)}"
    response["X-Content-Type-Options"] = "nosniff"
    return response
