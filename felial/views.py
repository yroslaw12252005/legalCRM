from django.shortcuts import redirect, render
from felial.models import Felial
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
