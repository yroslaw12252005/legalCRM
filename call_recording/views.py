from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from leads.access import status_matches

from .models import CallRecording


ALLOWED_STATUSES = ("Директор КЦ", "Директор ЮПП", "Администратор")


def can_view_recordings(user):
    return user.is_authenticated and status_matches(user.status, *ALLOWED_STATUSES)


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

    recording = get_object_or_404(CallRecording, id=pk, companys=request.user.companys)
    return redirect(recording.file_url)

