from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from .forms import AddEmployeesForm, EmployeeUpdateForm, SoloProfileUpdateForm
from .models import User


def _uses_solo_mode(user):
    company = getattr(user, "companys", None)
    return bool(company and company.is_solo)


@login_required
def employees(request):
    if _uses_solo_mode(request.user):
        messages.info(request, "В самостоятельном режиме используется одна учётная запись")
        return redirect("current_applications")
    if request.user.status != "Администратор":
        messages.error(request, "Недостаточно прав")
        return redirect("all_leads")
    get_employees = User.objects.filter(
        companys=request.user.companys,
        felial=request.user.felial,
        is_active=True,
    )
    return render(request, "employees.html", {"employees": get_employees})


@login_required
def delete_employee(request, pk):
    if _uses_solo_mode(request.user):
        messages.warning(request, "Единственную учётную запись нельзя удалить")
        return redirect("current_applications")
    if request.user.status != "Администратор":
        messages.error(request, "Недостаточно прав")
        return redirect("all_leads")

    del_employee = get_object_or_404(User, id=pk, companys=request.user.companys)
    del_employee.is_active = False
    del_employee.save(update_fields=["is_active"])
    messages.success(request, "Сотрудник деактивирован")
    return redirect("all_leads")


@login_required
def register_employees(request):
    if _uses_solo_mode(request.user):
        messages.info(request, "Добавление сотрудников доступно после перехода в режим компании")
        return redirect("current_applications")
    if request.user.status not in {"Администратор", "Директор КЦ", "Директор ЮПП"}:
        messages.error(request, "Недостаточно прав")
        return redirect("all_leads")
    form = AddEmployeesForm(request.POST or None, user=request.user)
    if request.method == "POST":
        form = AddEmployeesForm(request.POST, user=request.user)

        if form.is_valid():
            add_user = form.save(commit=False)
            add_user.companys = request.user.companys
            add_user.is_account_blocked = request.user.companys.is_subscription_blocked
            add_user.save()
            messages.success(request, "Пользователь зарегистрирован")
            return redirect("all_leads")

        messages.error(request, "Ошибка при регистрации")

    return render(request, "register_employees.html", {"form": form, "is_editing": False})


@login_required
def update_employees(request, pk):
    if request.user.status != "Администратор":
        messages.error(request, "Недостаточно прав")
        return redirect("all_leads")

    employee = get_object_or_404(User, id=pk, companys=request.user.companys)

    if request.method == "POST":
        form = EmployeeUpdateForm(request.POST, instance=employee, user=request.user)
        if form.is_valid():
            updated = form.save()
            messages.success(request, f"Сотрудник '{updated.username}' обновлен")
            return redirect("all_leads")
    else:
        form = EmployeeUpdateForm(instance=employee, user=request.user)

    return render(request, "register_employees.html", {"form": form, "is_editing": True})


@login_required
def update_profile(request):
    if not _uses_solo_mode(request.user):
        messages.warning(request, "Личный профиль доступен для самостоятельного режима")
        return redirect("current_applications")

    form = SoloProfileUpdateForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        password_changed = bool(form.cleaned_data.get("password"))
        user = form.save()
        if password_changed:
            update_session_auth_hash(request, user)
        messages.success(request, "Профиль обновлён")
        return redirect("update_profile")

    return render(request, "profile_edit.html", {"form": form})


@never_cache
@login_required
def account_blocked(request):
    return render(request, "account_blocked.html", status=403)
