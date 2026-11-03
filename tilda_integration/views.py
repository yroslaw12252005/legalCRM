import secrets
from datetime import timedelta

from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from leads.access import status_matches

from .forms import TildaIntegrationForm
from .models import TildaIntegration
from .services import (
    TildaWebhookError,
    first_value,
    parse_payload,
    process_submission,
    hash_secret,
    secret_matches,
    supplied_token,
)


WEBHOOK_RATE_LIMIT = getattr(settings, "TILDA_WEBHOOK_RATE_LIMIT", 120)
WEBHOOK_RATE_WINDOW_SECONDS = 60


def _new_secret():
    return "tld_" + secrets.token_urlsafe(32)


def _bump(integration_id, field, *, touch=False):
    updates = {field: F(field) + 1}
    if touch:
        updates["last_request_at"] = timezone.now()
    TildaIntegration.objects.filter(pk=integration_id).update(**updates)


def _rate_limited(public_id):
    now = timezone.now()
    with transaction.atomic():
        integration = TildaIntegration.objects.select_for_update().get(public_id=public_id)
        window_expired = (
            integration.rate_window_started_at is None
            or (now - integration.rate_window_started_at).total_seconds() >= WEBHOOK_RATE_WINDOW_SECONDS
        )
        if window_expired:
            integration.rate_window_started_at = now
            integration.rate_window_count = 1
        else:
            integration.rate_window_count += 1
        integration.save(update_fields=["rate_window_started_at", "rate_window_count"])
        return integration.rate_window_count > WEBHOOK_RATE_LIMIT


@csrf_exempt
@require_POST
def tilda_webhook(request, public_id):
    integration = get_object_or_404(
        TildaIntegration.objects.select_related("company", "branch"),
        public_id=public_id,
        is_active=True,
    )

    try:
        payload = parse_payload(request)
    except TildaWebhookError as error:
        _bump(integration.id, "total_rejected")
        return HttpResponse(error.code, status=error.status)

    token = supplied_token(request, payload)
    previous_key_is_valid = bool(
        integration.previous_secret_hash
        and integration.previous_secret_valid_until
        and integration.previous_secret_valid_until >= timezone.now()
        and secret_matches(token, integration.previous_secret_hash)
    )
    if not secret_matches(token, integration.secret_hash) and not previous_key_is_valid:
        _bump(integration.id, "total_auth_failed")
        return HttpResponse("forbidden", status=403)

    if _rate_limited(public_id):
        return HttpResponse("rate_limited", status=429)

    _bump(integration.id, "total_received", touch=True)
    if first_value(payload, "test"):
        return HttpResponse("ok")

    try:
        result = process_submission(integration, payload)
    except TildaWebhookError as error:
        _bump(integration.id, "total_rejected")
        return HttpResponse(error.code, status=error.status)

    if result.duplicate:
        _bump(integration.id, "total_duplicates")
    else:
        _bump(integration.id, "total_processed")
    return HttpResponse("ok")


def _company_admin_or_404(request):
    if not request.user.is_authenticated or not request.user.companys_id:
        raise Http404
    if not status_matches(request.user.status, "Администратор"):
        raise Http404
    return request.user.companys


def _integration_rows(request, company):
    rows = []
    queryset = TildaIntegration.objects.filter(company=company).select_related("branch")
    for integration in queryset:
        rows.append(
            {
                "integration": integration,
                "webhook_url": request.build_absolute_uri(
                    reverse("tilda_webhook", args=[integration.public_id])
                ),
            }
        )
    return rows


def _render_integrations(request, company, *, form=None, new_secret=None, secret_integration=None):
    return render(
        request,
        "tilda_integration/integrations.html",
        {
            "rows": _integration_rows(request, company),
            "form": form or TildaIntegrationForm(company=company),
            "new_secret": new_secret,
            "secret_integration": secret_integration,
        },
    )


@login_required
def integration_list(request):
    company = _company_admin_or_404(request)
    return _render_integrations(request, company)


@login_required
@require_POST
def integration_create(request):
    company = _company_admin_or_404(request)
    form = TildaIntegrationForm(request.POST, company=company)
    if not form.is_valid():
        return _render_integrations(request, company, form=form)

    secret = _new_secret()
    integration = form.save(commit=False)
    integration.secret_hash = hash_secret(secret)
    integration.created_by = request.user
    integration.save()
    messages.success(request, "Подключение Tilda создано. Сохраните ключ — повторно он не показывается.")
    return _render_integrations(
        request,
        company,
        new_secret=secret,
        secret_integration=integration,
    )


@login_required
def integration_edit(request, pk):
    company = _company_admin_or_404(request)
    integration = get_object_or_404(TildaIntegration, pk=pk, company=company)
    form = TildaIntegrationForm(
        request.POST or None,
        instance=integration,
        company=company,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Настройки подключения сохранены.")
        return redirect("tilda_integration_list")
    return render(
        request,
        "tilda_integration/integration_edit.html",
        {"form": form, "integration": integration},
    )


@login_required
@require_POST
def integration_rotate_secret(request, pk):
    company = _company_admin_or_404(request)
    integration = get_object_or_404(TildaIntegration, pk=pk, company=company)
    secret = _new_secret()
    integration.previous_secret_hash = integration.secret_hash
    integration.previous_secret_valid_until = timezone.now() + timedelta(minutes=10)
    integration.secret_hash = hash_secret(secret)
    integration.save(
        update_fields=[
            "secret_hash",
            "previous_secret_hash",
            "previous_secret_valid_until",
            "updated_at",
        ]
    )
    messages.warning(request, "Ключ заменён. Старый ключ продолжит работать ещё 10 минут.")
    return _render_integrations(
        request,
        company,
        new_secret=secret,
        secret_integration=integration,
    )


@login_required
@require_POST
def integration_toggle(request, pk):
    company = _company_admin_or_404(request)
    integration = get_object_or_404(TildaIntegration, pk=pk, company=company)
    integration.is_active = not integration.is_active
    integration.save(update_fields=["is_active", "updated_at"])
    state = "включено" if integration.is_active else "отключено"
    messages.success(request, f"Подключение {state}.")
    return redirect("tilda_integration_list")
