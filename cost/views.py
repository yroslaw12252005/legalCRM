from django.shortcuts import render
from django.contrib import messages

from .forms import Surcharge_form


def cost(request):
    if request.user.is_authenticated:
        surcharge_form = Surcharge_form(request.POST or None)
        if surcharge_form.is_valid():
            surcharge_form.save()
            messages.success(request, f"Доплата добавленна")
        return render(request, "surcharge.html",
                  {"surcharge_form": surcharge_form})