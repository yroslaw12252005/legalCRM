from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import AddEmployeesForm, EmployeeUpdateForm
from .models import User


@login_required
def employees(request):
    if request.user.status not in {"Администратор", "Директор КЦ", "Директор ЮПП"}:
        messages.error(request, "Недостаточно прав")
        return redirect("all_leads")
    get_employees = User.objects.filter(companys=request.user.companys, felial=request.user.felial)
    return render(request, "employees.html", {"employees": get_employees})


@login_required
def delete_employee(request, pk):
    if request.user.status not in {"Администратор", "Директор КЦ", "Директор ЮПП"}:
        messages.error(request, "Недостаточно прав")
        return redirect("all_leads")

    del_employee = get_object_or_404(User, id=pk, companys=request.user.companys)
    del_employee.delete()
    messages.success(request, "Сотрудник удален")
    return redirect("all_leads")


@login_required
def register_employees(request):
    if request.user.status not in {"Администратор", "Директор КЦ", "Директор ЮПП"}:
        messages.error(request, "Недостаточно прав")
        return redirect("all_leads")
    form = AddEmployeesForm(request.POST or None, user=request.user)
    if request.method == "POST":
        form = AddEmployeesForm(request.POST, user=request.user)

        if form.is_valid():
            add_user = form.save(commit=False)
            add_user.companys = request.user.companys
            add_user.save()
            messages.success(request, "Пользователь зарегистрирован")
            return redirect("all_leads")

        messages.error(request, "Ошибка при регистрации")

    return render(request, "register_employees.html", {"form": form})


@login_required
def update_employees(request, pk):
    if request.user.status not in {"Администратор", "Директор КЦ", "Директор ЮПП"}:
        messages.error(request, "Недостаточно прав")
        return redirect("all_leads")

    employee = get_object_or_404(User, id=pk, companys=request.user.companys)

    if request.method == "POST":
        form = EmployeeUpdateForm(request.POST, instance=employee)
        if form.is_valid():
            updated = form.save()
            messages.success(request, f"Сотрудник '{updated.username}' обновлен")
            return redirect("all_leads")
    else:
        form = EmployeeUpdateForm(instance=employee)

    return render(request, "register_employees.html", {"form": form})
