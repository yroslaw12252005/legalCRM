from django.shortcuts import render
from django.contrib import messages
from django.db.models import Sum

from .forms import Surcharge_form

from leads.models import Record
from accounts.models import User

def cost(request, pk):
    get_record_single = Record.objects.get(id=pk)
    if request.user.is_authenticated:
        get_surcharge_form = Surcharge_form(request.POST or None)
        if get_surcharge_form.is_valid():
            add_surcharge_form = get_surcharge_form.save(commit=False)
            add_surcharge_form.record = get_record_single  # The logged-in user
            add_surcharge_form.save()
            messages.success(request, f"Доплата добавленна")
        return render(request, "surcharge.html",
                  {"surcharge_form": get_surcharge_form})

def calculating_salaries(request, pk):
    get_employee = User.objects.get(id=pk)
    if get_employee.type_zp == "Процент":
        return percent(request, get_employee)
    elif get_employee.type_zp == "Ставка":
        return bet(request, get_employee)
    elif get_employee.type_zp == "Процент + Ставка":
        return percent_and_bet(request, get_employee)

def percent(request, get_employee):
    if get_employee.status == "Юрист пирвичник":
        get_and_sum_cost_record = Record.objects.filter(employees_UPP=get_employee.id).aggregate(Sum('cost'))
    elif get_employee.status == "Оператор кц":
        get_and_sum_cost_record = Record.objects.filter(employees_KC=get_employee.id).aggregate(Sum('cost'))
    else:
        get_and_sum_cost_record = {"cost__sum":None}

    if get_and_sum_cost_record["cost__sum"] == None:
        get_and_sum_cost_record["cost__sum"] = 0.0
    calculation_salary_user  = float(get_and_sum_cost_record['cost__sum'])*float(get_employee.percent)
    return render(request, "user_inform.html",
                  {"zp": calculation_salary_user, "cash": get_and_sum_cost_record, "employee":get_employee})

def bet(request, get_employee):
    get_salary_user = get_employee.bet
    get_and_sum_cost_record = "Не предусмотренно"
    return render(request, "user_inform.html",
                  {"zp": get_salary_user, "cash": get_and_sum_cost_record, "employee":get_employee})

def percent_and_bet(request, get_employee):
    if get_employee.status == "Юрист пирвичник":
        get_and_sum_cost_record = Record.objects.filter(employees_UPP=get_employee.id).aggregate(Sum('cost'))

    elif get_employee.status == "Оператор":
        get_and_sum_cost_record = Record.objects.filter(employees_KC=get_employee.id).aggregate(Sum('cost'))
    else:
        get_and_sum_cost_record = {"cost__sum":None}

    if get_and_sum_cost_record["cost__sum"] == None:
        get_and_sum_cost_record["cost__sum"] = 0.0


    calculation_salary_employee = float(get_and_sum_cost_record['cost__sum']) * float(get_employee.percent)+float(get_employee.bet)
    return render(request, "user_inform.html",
                  {"zp": calculation_salary_employee, "cash": get_and_sum_cost_record, "employee":get_employee})