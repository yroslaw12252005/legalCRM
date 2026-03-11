from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from leads.models import Record

from .forms import Surcharge_form
from .models import Surcharge


@login_required
def cost(request, pk):
    get_record_single = get_object_or_404(Record, id=pk, companys=request.user.companys)
    if request.user.status not in {"Юрист пирвичник", "Менеджер", "Администратор", "Директор ЮПП"}:
        messages.warning(request, "Нет прав для внесения доплаты")
        return redirect("record", pk=pk)
    if request.user.status == "Юрист пирвичник" and get_record_single.employees_UPP != request.user.username:
        messages.warning(request, "Нет прав для внесения доплаты")
        return redirect("record", pk=pk)
    get_surcharge_form = Surcharge_form(request.POST or None)
    if get_surcharge_form.is_valid():
        add_surcharge_form = get_surcharge_form.save(commit=False)
        add_surcharge_form.record = get_record_single
        add_surcharge_form.responsible = request.user
        add_surcharge_form.save()
        messages.success(request, "Доплата добавлена")

    return render(request, "surcharge.html", {"surcharge_form": get_surcharge_form})


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
def delete_surcharge(request, pk):
    if request.user.status != "Администратор":
        messages.warning(request, "Нет прав для удаления доплаты")
        return redirect("home")
    surcharge = get_object_or_404(Surcharge, id=pk, record__companys=request.user.companys)
    record_id = surcharge.record_id
    surcharge.delete()
    messages.success(request, "Доплата удалена")
    return redirect("record", pk=record_id)


@login_required
def percent(request, get_employee):
    if get_employee.status == "Юрист пирвичник":
        get_and_sum_cost_record = Record.objects.filter(
            employees_UPP=get_employee.username,
            companys=get_employee.companys,
        ).aggregate(Sum("cost"))
    elif get_employee.status == "Оператор":
        get_and_sum_cost_record = Record.objects.filter(
            employees_KC=get_employee.username,
            companys=get_employee.companys,
        ).aggregate(Sum("cost"))
    else:
        get_and_sum_cost_record = {"cost__sum": None}

    if get_and_sum_cost_record["cost__sum"] is None:
        get_and_sum_cost_record["cost__sum"] = 0.0

    calculation_salary_user = float(get_and_sum_cost_record["cost__sum"]) * float(get_employee.percent or 0)

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
    if get_employee.status == "Юрист пирвичник":
        get_and_sum_cost_record = Record.objects.filter(
            employees_UPP=get_employee.username,
            companys=get_employee.companys,
        ).aggregate(Sum("cost"))
    elif get_employee.status == "Оператор":
        get_and_sum_cost_record = Record.objects.filter(
            employees_KC=get_employee.username,
            companys=get_employee.companys,
        ).aggregate(Sum("cost"))
    else:
        get_and_sum_cost_record = {"cost__sum": None}

    if get_and_sum_cost_record["cost__sum"] is None:
        get_and_sum_cost_record["cost__sum"] = 0.0

    calculation_salary_employee = float(get_and_sum_cost_record["cost__sum"]) * float(get_employee.percent or 0) + float(get_employee.bet or 0)
    return render(
        request,
        "user_inform.html",
        {"zp": calculation_salary_employee, "cash": get_and_sum_cost_record, "employee": get_employee},
    )
