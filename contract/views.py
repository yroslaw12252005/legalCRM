from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from leads.access import status_matches
from leads.models import Record

from .forms import ContractForm
from .models import Contract


def _can_manage_contracts(user):
    return status_matches(user.status, "Менеджер", "Администратор", "Директор ЮПП")


@login_required
def add_contract(request, record_id):
    record = get_object_or_404(Record, id=record_id, companys=request.user.companys)
    if not _can_manage_contracts(request.user):
        messages.warning(request, "Нет прав для создания договора")
        return redirect("record", pk=record.id)

    form = ContractForm(request.POST or None, instance=Contract(record=record))
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Договор создан")
        return redirect("record", pk=record.id)

    return render(
        request,
        "contract/contract_form.html",
        {"form": form, "record": record, "page_title": "Создание договора"},
    )


@login_required
def edit_contract(request, pk):
    contract = get_object_or_404(
        Contract.objects.select_related("record"),
        id=pk,
        record__companys=request.user.companys,
    )
    if not _can_manage_contracts(request.user):
        messages.warning(request, "Нет прав для редактирования договора")
        return redirect("record", pk=contract.record_id)

    form = ContractForm(request.POST or None, instance=contract)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Договор обновлён")
        return redirect("record", pk=contract.record_id)

    return render(
        request,
        "contract/contract_form.html",
        {"form": form, "record": contract.record, "contract": contract, "page_title": "Редактирование договора"},
    )

