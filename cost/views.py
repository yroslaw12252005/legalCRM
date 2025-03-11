from django.shortcuts import render
from django.contrib import messages
from django.db.models import Sum

from .forms import Surcharge_form

from leads.models import Record
from accounts.models import User

def cost(request, pk):
    record = Record.objects.get(id=pk)
    if request.user.is_authenticated:
        surcharge_form = Surcharge_form(request.POST or None)
        if surcharge_form.is_valid():
            add_surcharge = surcharge_form.save(commit=False)
            add_surcharge.record = record  # The logged-in user
            add_surcharge.save()
            messages.success(request, f"Доплата добавленна")
        return render(request, "surcharge.html",
                  {"surcharge_form": surcharge_form})

def calculating_salaries(request, pk):
    user = User.objects.get(id=pk)
    if user.type_zp == "Процент":
        return percent(request, user)
    elif user.type_zp == "Ставка":
        return bet(request, user)
    elif user.type_zp == "Процент + Ставка":
        return percent_and_bet(request, user)

def percent(request, user):
    if user.status == "Юрист пирвичник":
        cash = Record.objects.filter(employees_UPP=user.id).aggregate(Sum('cost'))
    elif user.status == "Оператор кц":
        cash = Record.objects.filter(employees_KC=user.id).aggregate(Sum('cost'))

    zp = float(cash['cost__sum'])*float(user.percent)
    return render(request, "user_inform.html",
                  {"zp": zp, "cash":cash})

def bet(request, user):
    zp = user.bet
    cash = "Не предусмотренно"
    return render(request, "user_inform.html",
                  {"zp": zp, "cash": cash})

def percent_and_bet(request, user):
    if user.status == "Юрист пирвичник":
        cash = Record.objects.filter(employees_UPP=user.id).aggregate(Sum('cost'))
    elif user.status == "Оператор":
        cash = Record.objects.filter(employees_KC=user.id).aggregate(Sum('cost'))

    zp = float(cash['cost__sum']) * float(user.percent)+float(user.bet)
    return render(request, "user_inform.html",
                  {"zp": zp, "cash": cash})