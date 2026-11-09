from datetime import date, datetime
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
from .xlsx_export import build_salary_workbook


MONTH_NAMES = (
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
)
SALARY_ACCESS_ROLES = ("Администратор", "Менеджер")
PRIMARY_LAWYER_ROLE = "Юрист пирвичник"
REPRESENTATIVE_EMPLOYEE_ROLES = ("Представитель", "ОП")
BRANCH_SALARY_ROLES = (
    "Администратор",
    "Менеджер",
    "Директор",
    "Директор КЦ",
    "Директор ЮПП",
    "Директор представителей",
)
EXPORT_SALARY_ROLES = (
    PRIMARY_LAWYER_ROLE,
    *REPRESENTATIVE_EMPLOYEE_ROLES,
    "Менеджер",
    "Директор",
    "Директор КЦ",
    "Директор ЮПП",
    "Директор представителей",
)


def _has_salary_access(user):
    return status_matches(user.status, *SALARY_ACCESS_ROLES)


def _salary_access_required(request):
    if _has_salary_access(request.user):
        return None
    messages.error(request, "Раздел зарплаты доступен только администратору и менеджеру")
    return redirect("all_leads")


def _next_month(value):
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1, day=1)
    return value.replace(month=value.month + 1, day=1)


def _selected_period(request):
    now = timezone.now()
    today = timezone.localdate() if timezone.is_aware(now) else date.today()
    raw_month = request.GET.get("month", "")
    try:
        month_start = datetime.strptime(raw_month, "%Y-%m").date().replace(day=1)
    except (TypeError, ValueError):
        month_start = today.replace(day=1)

    period = request.GET.get("period")
    if period not in {"1", "2"}:
        period = "1" if today.day <= 15 else "2"
    if period == "1":
        period_start = month_start
        period_end = month_start.replace(day=16)
    else:
        period_start = month_start.replace(day=16)
        period_end = _next_month(month_start)

    last_inclusive = date.fromordinal(period_end.toordinal() - 1)
    return {
        "month_start": month_start,
        "period": period,
        "period_start": period_start,
        "period_end": period_end,
        "month_value": month_start.strftime("%Y-%m"),
        "month_label": f"{MONTH_NAMES[month_start.month]} {month_start.year}",
        "period_label": f"{period_start:%d.%m.%Y}–{last_inclusive:%d.%m.%Y}",
    }


def _employee_contracts(employee):
    contracts = Contract.objects.filter(record__companys=employee.companys)
    if status_matches(employee.status, PRIMARY_LAWYER_ROLE):
        return contracts.filter(
            Q(record__lawyer=employee)
            | Q(record__lawyer__isnull=True, record__employees_UPP=employee.username)
        )
    if status_matches(employee.status, *REPRESENTATIVE_EMPLOYEE_ROLES):
        return contracts.filter(
            record__representative=True,
            record__employees_REP=employee.username,
        )
    if status_matches(employee.status, "Оператор"):
        return contracts.filter(record__employees_KC=employee.username)
    if status_matches(employee.status, *BRANCH_SALARY_ROLES):
        if not employee.felial_id:
            return contracts.none()
        return contracts.filter(record__felial_id=employee.felial_id)
    return contracts.none()


def _paid_surcharges(contracts, period_start, period_end):
    return Surcharge.objects.filter(contract__in=contracts, is_paid=True).filter(
        Q(paid_at__date__gte=period_start, paid_at__date__lt=period_end)
        | Q(
            paid_at__isnull=True,
            dat__date__gte=period_start,
            dat__date__lt=period_end,
        )
    )


def _period_salary_base(employee, period_start, period_end, include_details=False):
    # Salary is accrued only for leads that were transferred to a representative.
    contracts = _employee_contracts(employee).filter(record__representative=True)
    initial_payments = contracts.filter(
        contract_date__gte=period_start,
        contract_date__lt=period_end,
    )
    paid_surcharges = _paid_surcharges(contracts, period_start, period_end)

    initial_total = initial_payments.aggregate(
        total=Sum("initial_payment")
    )["total"] or Decimal("0")
    surcharge_total = paid_surcharges.aggregate(total=Sum("cost"))["total"] or Decimal("0")
    base_total = initial_total + surcharge_total
    result = {
        "initial_payments": initial_total,
        "surcharge_payments": surcharge_total,
        "base_total": base_total,
        "contracts_count": initial_payments.count(),
        "surcharges_count": paid_surcharges.count(),
    }

    if include_details:
        payment_rows = []
        for contract in initial_payments.select_related("record").order_by("contract_date", "id"):
            payment_rows.append({
                "date": contract.contract_date,
                "client": contract.record.name,
                "contract_number": contract.number,
                "payment_type": "Первоначальный взнос",
                "is_representation": contract.record.representative,
                "amount": contract.initial_payment,
            })
        for surcharge in paid_surcharges.select_related("contract__record").order_by("paid_at", "dat", "id"):
            amount = surcharge.cost or Decimal("0")
            payment_rows.append({
                "date": (surcharge.paid_at or surcharge.dat).date(),
                "client": surcharge.contract.record.name,
                "contract_number": surcharge.contract.number,
                "payment_type": "Доплата",
                "is_representation": surcharge.contract.record.representative,
                "amount": amount,
            })
        payment_rows.sort(key=lambda row: (row["date"], row["contract_number"]))
        result["payment_rows"] = payment_rows
    return result


def _salary_calculation(employee, period_start, period_end, include_details=False):
    salary_base = _period_salary_base(employee, period_start, period_end, include_details)
    percent_value = employee.percent or Decimal("0")
    bet_value = employee.bet or Decimal("0")
    salary_type = {
        "Ставка": User.SALARY_FIXED,
        "Процент + Ставка": User.SALARY_COMBINED,
        "Оклад+Процент": User.SALARY_COMBINED,
    }.get(employee.type_zp, employee.type_zp)
    uses_percent = salary_type in {User.SALARY_PERCENT, User.SALARY_COMBINED}
    uses_fixed = salary_type in {User.SALARY_FIXED, User.SALARY_COMBINED}
    period_fixed_salary = bet_value / Decimal("2") if uses_fixed else Decimal("0")
    percent_salary = (
        salary_base["base_total"] * percent_value / Decimal("100")
        if uses_percent
        else Decimal("0")
    )
    salary = period_fixed_salary + percent_salary
    if salary_type == User.SALARY_FIXED:
        calculation_amount = period_fixed_salary
    elif uses_percent:
        calculation_amount = salary_base["base_total"]
    else:
        calculation_amount = Decimal("0")

    if include_details:
        for payment in salary_base["payment_rows"]:
            payment["rate"] = percent_value if uses_percent else Decimal("0")
            payment["salary"] = (
                payment["amount"] * percent_value / Decimal("100")
                if uses_percent
                else Decimal("0")
            )

    return {
        **salary_base,
        "salary": salary,
        "calculation_amount": calculation_amount,
        "percent_value": percent_value,
        "bet_value": bet_value,
        "salary_type": salary_type,
        "uses_percent": uses_percent,
        "uses_fixed": uses_fixed,
        "period_fixed_salary": period_fixed_salary,
        "percent_salary": percent_salary,
    }


@login_required
def salary_list(request):
    access_response = _salary_access_required(request)
    if access_response:
        return access_response
    selected = _selected_period(request)
    employees = User.objects.filter(
        companys=request.user.companys,
        is_active=True,
    ).order_by("username", "id")
    salary_rows = []
    for employee in employees:
        calculation = _salary_calculation(
            employee, selected["period_start"], selected["period_end"]
        )
        salary_rows.append({"employee": employee, **calculation})
    return render(request, "salary_list.html", {"salary_rows": salary_rows, **selected})


@login_required
def salary_export(request):
    access_response = _salary_access_required(request)
    if access_response:
        return access_response

    selected = _selected_period(request)
    employees = User.objects.filter(
        companys=request.user.companys,
        is_active=True,
    ).order_by("username", "id")
    payroll_employees = [
        employee for employee in employees
        if status_matches(employee.status, *EXPORT_SALARY_ROLES)
    ]
    payroll_rows = []
    for employee in payroll_employees:
        calculation = _salary_calculation(
            employee, selected["period_start"], selected["period_end"]
        )
        payroll_rows.append({"name": employee.username, "status": employee.status, **calculation})
    content = build_salary_workbook(
        f"Ведомость за период {selected['period_label']}",
        payroll_rows,
    )
    filename = f"salary_{selected['month_value']}_period_{selected['period']}.xlsx"
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


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
    if status_matches(request.user.status, "Юрист пирвичник") and not record.is_assigned_to_lawyer(request.user):
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
    access_response = _salary_access_required(request)
    if access_response:
        return access_response
    employee = get_object_or_404(User, id=pk, companys=request.user.companys, is_active=True)
    selected = _selected_period(request)
    calculation = _salary_calculation(
        employee,
        selected["period_start"],
        selected["period_end"],
        include_details=True,
    )
    return render(
        request,
        "user_inform.html",
        {
            "employee": employee,
            "zp": calculation["salary"],
            **selected,
            **calculation,
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
