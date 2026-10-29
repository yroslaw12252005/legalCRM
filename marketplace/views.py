from urllib.parse import urlencode
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from leads.forms import ExcelUploadForm

from .excel import build_excel_template_bytes, extract_leads_from_excel
from .forms import LeadDistributionForm
from .models import MarketplaceLead
from .services import distribute_marketplace_leads


def _require_yrik(user):
    if user.username != "Yrik":
        raise PermissionDenied


@login_required
def download_excel_template(request):
    _require_yrik(request.user)
    response = HttpResponse(
        build_excel_template_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="marketplace_leads_template.xlsx"'
    return response


@login_required
def import_leads_from_excel(request):
    _require_yrik(request.user)
    form = ExcelUploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        try:
            leads, skipped_rows = extract_leads_from_excel(form.cleaned_data["file"])
        except (ValueError, KeyError, BadZipFile, ParseError):
            form.add_error("file", "Не удалось прочитать Excel-файл. Скачайте шаблон и заполните его заново.")
        else:
            marketplace_leads = [
                MarketplaceLead(name=lead["name"], phone=lead["phone"])
                for lead in leads
            ]
            MarketplaceLead.objects.bulk_create(marketplace_leads)
            message = f"На биржу загружено заявок: {len(marketplace_leads)}"
            if skipped_rows:
                message += f". Пропущено строк без имени или телефона: {skipped_rows}"
            messages.success(request, message)
            return redirect("marketplace_distribution")

    return render(request, "marketplace/excel_import.html", {"form": form})


@login_required
def distribution_list(request):
    _require_yrik(request.user)
    selected_status = request.GET.get("status", "all")
    leads = MarketplaceLead.objects.select_related("buyer")
    if selected_status in {MarketplaceLead.STATUS_AVAILABLE, MarketplaceLead.STATUS_SOLD}:
        leads = leads.filter(status=selected_status)

    if request.method == "POST":
        selected_ids = sorted({int(value) for value in request.POST.getlist("selected_leads") if value.isdigit()})
        if not selected_ids:
            messages.warning(request, "Выберите хотя бы одну непроданную заявку")
            return redirect("marketplace_distribution")
        available_count = MarketplaceLead.objects.filter(
            id__in=selected_ids,
            status=MarketplaceLead.STATUS_AVAILABLE,
        ).count()
        if available_count != len(selected_ids):
            messages.warning(request, "В выбор попала уже проданная или удалённая заявка")
            return redirect("marketplace_distribution")
        confirm_url = reverse("marketplace_distribution_confirm")
        return redirect(f"{confirm_url}?{urlencode({'ids': ','.join(map(str, selected_ids))})}")

    page_obj = Paginator(leads, 100).get_page(request.GET.get("page"))
    return render(
        request,
        "marketplace/distribution_list.html",
        {
            "page_obj": page_obj,
            "leads": page_obj.object_list,
            "selected_status": selected_status,
            "available_count": MarketplaceLead.objects.filter(status=MarketplaceLead.STATUS_AVAILABLE).count(),
        },
    )


@login_required
def distribution_confirm(request):
    _require_yrik(request.user)
    initial_ids = request.GET.get("ids", "")
    form = LeadDistributionForm(request.POST or None, initial={"lead_ids": initial_ids})

    raw_ids = request.POST.get("lead_ids", initial_ids)
    selected_ids = [int(value) for value in raw_ids.split(",") if value.strip().isdigit()]
    selected_leads = MarketplaceLead.objects.filter(id__in=selected_ids).order_by("id")
    company_finances = {}
    for company in form.fields["company"].queryset:
        settings = company.lead_stream_settings
        wallet = getattr(company, "wallet", None)
        company_finances[str(company.pk)] = {
            "price": float(settings.lead_price),
            "budget": float(settings.remaining_budget),
            "balance": float(wallet.balance if wallet else 0),
        }

    if request.method == "POST" and form.is_valid():
        try:
            purchases, wallet_operation = distribute_marketplace_leads(
                form.cleaned_data["lead_ids"],
                form.cleaned_data["company"],
            )
        except ValidationError as error:
            form.add_error(None, error.messages[0])
        else:
            messages.success(
                request,
                f"Распределено заявок: {len(purchases)}. Списано: {wallet_operation.amount:.2f} ₽",
            )
            return redirect("marketplace_distribution")

    return render(
        request,
        "marketplace/distribution_confirm.html",
        {
            "form": form,
            "selected_leads": selected_leads,
            "company_finances": company_finances,
        },
    )
