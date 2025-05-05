from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .forms import AddEmployeesForm

from .models import User


def employees(request):
    get_employees = User.objects.filter(companys=request.user.companys, felial=request.user.felial)
    return render(request, "employees.html", {"employees": get_employees})

def delete_employee(request, pk):
    if request.user.is_authenticated:
        del_employee = User.objects.get(id=pk)
        del_employee.delete()
        messages.success(request, "Вы спешно удалил запись")
        return redirect("home")
    else:
        return redirect("home")


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

