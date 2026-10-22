from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from leads.access import status_matches
from leads.models import Record

from .forms import ContractForm, ContractSurchargeFormSet
from .models import Contract


def _can_manage_contracts(user):
    return status_matches(user.status, "Менеджер", "Администратор", "Директор ЮПП")


def _can_delete_existing_surcharges(user):
    return status_matches(user.status, "Администратор")


def _save_contract_with_surcharges(form, surcharge_formset, user):
    with transaction.atomic():
        contract = form.save()
        surcharge_formset.instance = contract
        surcharges = surcharge_formset.save(commit=False)
        for surcharge in surcharge_formset.deleted_objects:
            surcharge.delete()
        for surcharge in surcharges:
            if not surcharge.responsible_id:
                surcharge.responsible = user
            surcharge.save()
        surcharge_formset.save_m2m()
    return contract


def _contract_form_context(form, surcharge_formset, record, page_title, contract=None, user=None):
    return {
        "form": form,
        "surcharge_formset": surcharge_formset,
        "record": record,
        "contract": contract,
        "page_title": page_title,
        "can_delete_existing_surcharges": bool(user and _can_delete_existing_surcharges(user)),
    }


@login_required
def add_contract(request, record_id):
    record = get_object_or_404(Record, id=record_id, companys=request.user.companys)
    if not _can_manage_contracts(request.user):
        messages.warning(request, "Нет прав для создания договора")
        return redirect("record", pk=record.id)

    contract = Contract(record=record)
    form = ContractForm(request.POST or None, instance=contract)
    form_valid = request.method == "POST" and form.is_valid()
    expected_total = None
    if form_valid:
        expected_total = form.cleaned_data["amount"] - form.cleaned_data["initial_payment"]
    surcharge_formset = ContractSurchargeFormSet(
        request.POST or None,
        instance=contract,
        prefix="surcharges",
        expected_total=expected_total,
        allow_existing_deletes=_can_delete_existing_surcharges(request.user),
    )
    if form_valid and surcharge_formset.is_valid():
        _save_contract_with_surcharges(form, surcharge_formset, request.user)
        messages.success(request, "Договор создан")
        return redirect("record", pk=record.id)

    return render(
        request,
        "contract/contract_form.html",
        _contract_form_context(
            form,
            surcharge_formset,
            record,
            "Создание договора",
            user=request.user,
        ),
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
    form_valid = request.method == "POST" and form.is_valid()
    expected_total = contract.remaining_amount
    if form_valid:
        expected_total = form.cleaned_data["amount"] - form.cleaned_data["initial_payment"]
    surcharge_formset = ContractSurchargeFormSet(
        request.POST or None,
        instance=contract,
        prefix="surcharges",
        expected_total=expected_total,
        allow_existing_deletes=_can_delete_existing_surcharges(request.user),
    )
    if form_valid and surcharge_formset.is_valid():
        _save_contract_with_surcharges(form, surcharge_formset, request.user)
        messages.success(request, "Договор обновлён")
        return redirect("record", pk=contract.record_id)

    return render(
        request,
        "contract/contract_form.html",
        _contract_form_context(
            form,
            surcharge_formset,
            contract.record,
            "Редактирование договора",
            contract=contract,
            user=request.user,
        ),
    )

