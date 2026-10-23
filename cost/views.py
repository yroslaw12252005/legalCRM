from datetime import date, datetime, time
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from contract.models import Contract
from leads.access import status_matches

from .forms import Surcharge_form
from .models import Surcharge


MONTH_NAMES = (
    "",
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)


def _selected_month(request):
    raw_month = request.GET.get("month", "")
    try:
        return datetime.strptime(raw_month, "%Y-%m").date().replace(day=1)
    except (TypeError, ValueError):
        return date.today().replace(day=1)


def _next_month(value):
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1)
    return value.replace(month=value.month + 1)


def _employee_contracts(employee):
    contracts = Contract.objects.filter(record__companys=employee.companys)
    if status_matches(employee.status, "Юрист пирвичник"):
        return contracts.filter(record__employees_UPP=employee.username)
    if status_matches(employee.status, "Оператор"):
        return contracts.filter(record__employees_KC=employee.username)
    return contracts.none()


def _monthly_salary_base(employee, month_start):
    month_end = _next_month(month_start)
    contracts = _employee_contracts(employee)
    monthly_contracts = contracts.filter(
        contract_date__gte=month_start,
        contract_date__lt=month_end,
    )
    initial_payments = monthly_contracts.aggregate(total=Sum("initial_payment"))["total"] or Decimal("0")

    period_start = datetime.combine(month_start, time.min)
    period_end = datetime.combine(month_end, time.min)
    paid_surcharges = Surcharge.objects.filter(
        contract__in=contracts,
        is_paid=True,
    ).filter(
        Q(paid_at__gte=period_start, paid_at__lt=period_end)
        | Q(
            paid_at__isnull=True,
            dat__gte=period_start,
            dat__lt=period_end,
        )
    )
    surcharge_payments = paid_surcharges.aggregate(total=Sum("cost"))["total"] or Decimal("0")

    return {
        "initial_payments": initial_payments,
        "surcharge_payments": surcharge_payments,
        "base_total": initial_payments + surcharge_payments,
        "contracts_count": monthly_contracts.count(),
        "surcharges_count": paid_surcharges.count(),
    }


@login_required
def cost(request, pk):
    contract = get_object_or_404(
        Contract.objects.select_related("record"),
        id=pk,
        record__companys=request.user.companys,
    )
    record = contract.record
    if not status_matches(request.user.status, "Юрист пирвичник", "Менеджер", "Администратор", "Директор ЮПП"):
        messages.warning(request, "Нет прав для внесения доплаты")
        return redirect("record", pk=record.id)
    if status_matches(request.user.status, "Юрист пирвичник") and record.employees_UPP != request.user.username:
        messages.warning(request, "Нет прав для внесения доплаты")
        return redirect("record", pk=record.id)
    get_surcharge_form = Surcharge_form(request.POST or None)
    if request.method == "POST" and get_surcharge_form.is_valid():
        scheduled_total = contract.surcharges.aggregate(total=Sum("cost"))["total"] or 0
        surcharge_cost = get_surcharge_form.cleaned_data["cost"] or 0
        if scheduled_total + surcharge_cost > contract.surcharge_plan_amount:
            get_surcharge_form.add_error(
                "cost",
                f"Доплата превышает остаток по графику ({contract.surcharge_plan_amount - scheduled_total:.2f} руб.)",
            )
        else:
            add_surcharge_form = get_surcharge_form.save(commit=False)
            add_surcharge_form.contract = contract
            add_surcharge_form.responsible = request.user
            add_surcharge_form.save()
            messages.success(request, "Доплата добавлена")
            return redirect("record", pk=record.id)

    return render(
        request,
        "surcharge.html",
        {"surcharge_form": get_surcharge_form, "contract": contract, "record": record},
    )


@login_required
def calculating_salaries(request, pk):
    employee = get_object_or_404(User, id=pk, companys=request.user.companys)
    month_start = _selected_month(request)
    salary_base = _monthly_salary_base(employee, month_start)
    percent_value = employee.percent or Decimal("0")
    bet_value = employee.bet or Decimal("0")

    if employee.type_zp == "Процент":
        salary = salary_base["base_total"] * percent_value
    elif employee.type_zp in {"Ставка", "Оклад"}:
        salary = bet_value
    elif employee.type_zp == "Процент + Ставка":
        salary = salary_base["base_total"] * percent_value + bet_value
    else:
        return HttpResponse("Неизвестный тип зарплаты", status=400)

    return render(
        request,
        "user_inform.html",
        {
            "employee": employee,
            "zp": salary,
            "percent_value": percent_value,
            "bet_value": bet_value,
            "month_value": month_start.strftime("%Y-%m"),
            "month_label": f"{MONTH_NAMES[month_start.month]} {month_start.year}",
            **salary_base,
        },
    )


@login_required
@require_POST
def delete_surcharge(request, pk):
    if not status_matches(request.user.status, "Администратор"):
        messages.warning(request, "Нет прав для удаления доплаты")
        return redirect("all_leads")
    surcharge = get_object_or_404(
        Surcharge.objects.select_related("contract__record"),
        id=pk,
        contract__record__companys=request.user.companys,
    )
    record_id = surcharge.contract.record_id
    surcharge.delete()
    messages.success(request, "Доплата удалена")
    return redirect("record", pk=record_id)


@login_required
@require_POST
def mark_surcharge_paid(request, pk):
    if not status_matches(request.user.status, "Администратор", "Менеджер"):
        messages.warning(request, "Подтвердить внесение доплаты может только администратор или менеджер")
        return redirect("all_leads")

    surcharge = get_object_or_404(
        Surcharge.objects.select_related("contract__record"),
        id=pk,
        contract__record__companys=request.user.companys,
    )
    if not surcharge.is_paid:
        surcharge.is_paid = True
        surcharge.paid_at = timezone.now()
        surcharge.paid_by = request.user
        surcharge.save(update_fields=["is_paid", "paid_at", "paid_by"])
        messages.success(request, "Доплата отмечена как внесённая")
    return redirect("record", pk=surcharge.contract.record_id)
