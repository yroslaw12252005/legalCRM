from django.shortcuts import redirect, render
from felial.models import Felial
from leads.models import Record

from .forms import AddFelialForm
from django.contrib import messages

def add_felial(request):
    form = AddFelialForm(request.POST or None, request)
    if request.user.is_authenticated:
        if form.is_valid():
            add_felial = form.save(commit=False)
            add_felial.companys = request.user.companys  # The logged-in user
            add_felial.save()
            messages.success(request, f"Фелиал {add_felial.title} успешно создана")
            return redirect("home")
        return render(request, "add_felial.html", {"form": form})
    else:
        return redirect("home")

def felials(request):
    get_felials = Felial.objects.filter(companys=request.user.companys)
    return render(request, "felials.html", {"felials": get_felials})
def felial_info(request, id_feleal):
    get_recrds_felial = Record.objects.filter(companys=request.user.companys, felial=id_feleal)
    return render(request, "home.html", {"records": get_recrds_felial})