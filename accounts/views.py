from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .forms import AddEmployeesForm

from .models import User


def employees(request):
    user = User.objects.all()
    return render(request, "employees.html", {"users": user})

def register_employees(request):
    form = AddEmployeesForm()
    if request.method == "POST":
        form = AddEmployeesForm(request.POST)

        if form.is_valid():
            add_user = form.save(commit=False)
            add_user.companys = request.user.companys  # The logged-in user
            add_user.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            status = form.cleaned_data["status"]
            email = form.cleaned_data["email"]

            user = authenticate(username=username, email=email, status=status, password=password)
            login(request, user)
            messages.success(request, "Пользователь зарегестрирован")
            return redirect("home")
        else:
            messages.error(request, "An error occured during registration")

    return render(request, "register_employees.html", {"form": form})

