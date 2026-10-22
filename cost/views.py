from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from contract.models import Contract
from leads.access import status_matches

from .forms import Surcharge_form
from .models import Surcharge


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
        if scheduled_total + surcharge_cost > contract.remaining_amount:
            get_surcharge_form.add_error(
                "cost",
                f"Доплата превышает остаток по договору ({contract.remaining_amount - scheduled_total:.2f} руб.)",
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
    get_employee = get_object_or_404(User, id=pk, companys=request.user.companys)

    if get_employee.type_zp == "Процент":
        return percent(request, get_employee)
    if get_employee.type_zp in {"Ставка", "Оклад"}:
        return bet(request, get_employee)
    if get_employee.type_zp == "Процент + Ставка":
        return percent_and_bet(request, get_employee)

    return HttpResponse("Неизвестный тип зарплаты", status=400)


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


@login_required
def percent(request, get_employee):
    if status_matches(get_employee.status, "Юрист пирвичник"):
        amount_sum = Contract.objects.filter(
            record__employees_UPP=get_employee.username,
            record__companys=get_employee.companys,
        ).aggregate(Sum("amount"))["amount__sum"]
    elif status_matches(get_employee.status, "Оператор"):
        amount_sum = Contract.objects.filter(
            record__employees_KC=get_employee.username,
            record__companys=get_employee.companys,
        ).aggregate(Sum("amount"))["amount__sum"]
    else:
        amount_sum = None

    amount_sum = amount_sum or 0
    get_and_sum_cost_record = {"cost__sum": amount_sum}
    calculation_salary_user = float(amount_sum) * float(get_employee.percent or 0)

    return render(
        request,
        "user_inform.html",
        {"zp": calculation_salary_user, "cash": get_and_sum_cost_record, "employee": get_employee},
    )


@login_required
def bet(request, get_employee):
    get_salary_user = get_employee.bet
    get_and_sum_cost_record = "Не предусмотренно"
    return render(
        request,
        "user_inform.html",
        {"zp": get_salary_user, "cash": get_and_sum_cost_record, "employee": get_employee},
    )


@login_required
def percent_and_bet(request, get_employee):
    if status_matches(get_employee.status, "Юрист пирвичник"):
        amount_sum = Contract.objects.filter(
            record__employees_UPP=get_employee.username,
            record__companys=get_employee.companys,
        ).aggregate(Sum("amount"))["amount__sum"]
    elif status_matches(get_employee.status, "Оператор"):
        amount_sum = Contract.objects.filter(
            record__employees_KC=get_employee.username,
            record__companys=get_employee.companys,
        ).aggregate(Sum("amount"))["amount__sum"]
    else:
        amount_sum = None

    amount_sum = amount_sum or 0
    get_and_sum_cost_record = {"cost__sum": amount_sum}
    calculation_salary_employee = float(amount_sum) * float(get_employee.percent or 0) + float(get_employee.bet or 0)
    return render(
        request,
        "user_inform.html",
        {"zp": calculation_salary_employee, "cash": get_and_sum_cost_record, "employee": get_employee},
    )
