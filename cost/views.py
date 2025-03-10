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

def percent(request, pk):
    cash = Record.objects.filter(employees_UPP=pk).aggregate(Sum('cost'))
    percent_user = User.objects.get(id=pk)
    zp = float(cash['cost__sum'])*float(percent_user.percent)
    return render(request, "user_inform.html",
                  {"zp": zp, "cash":cash})
def bet(request, pk):
    pass
def percent_and_bet(request):
    pass