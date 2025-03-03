from django.shortcuts import render
from django.contrib import messages

from .forms import Surcharge_form

from leads.models import Record

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