from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from leads.models import Record
from felial.models import Felial

from .forms import AddFelialForm


@login_required
def add_felial(request):
    form = AddFelialForm(request.POST or None, request)
    if form.is_valid():
        add_felial = form.save(commit=False)
        add_felial.companys = request.user.companys
        add_felial.save()
        messages.success(request, f"Филиал {add_felial.title} успешно создан")
        return redirect("home")
    return render(request, "add_felial.html", {"form": form})


@login_required
def felials(request):
    get_felials = Felial.objects.filter(companys=request.user.companys)
    return render(request, "felials.html", {"felials": get_felials})


@login_required
def felial_info(request, id_feleal):
    get_recrds_felial = Record.objects.filter(companys=request.user.companys, felial=id_feleal)
    return render(request, "home.html", {"records": get_recrds_felial})
