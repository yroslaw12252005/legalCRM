from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import CompanyWallet, WalletTransaction


def _change_balance(wallet, amount, operation_type, comment=""):
    amount = Decimal(amount).quantize(Decimal("0.01"))
    if amount <= 0:
        raise ValidationError("Сумма операции должна быть больше нуля")

    with transaction.atomic():
        locked_wallet = CompanyWallet.objects.select_for_update().get(pk=wallet.pk)
        if operation_type == WalletTransaction.TYPE_DEPOSIT:
            new_balance = locked_wallet.balance + amount
        elif operation_type == WalletTransaction.TYPE_WITHDRAWAL:
            if locked_wallet.balance < amount:
                raise ValidationError("На балансе недостаточно средств")
            new_balance = locked_wallet.balance - amount
        else:
            raise ValidationError("Неизвестный тип денежной операции")

        locked_wallet.balance = new_balance
        locked_wallet.save(update_fields=("balance", "updated_at"))
        operation = WalletTransaction.objects.create(
            wallet=locked_wallet,
            operation_type=operation_type,
            amount=amount,
            balance_after=new_balance,
            comment=(comment or "").strip(),
        )
    return operation


def deposit(wallet, amount, comment=""):
    return _change_balance(wallet, amount, WalletTransaction.TYPE_DEPOSIT, comment)


def withdraw(wallet, amount, comment=""):
    return _change_balance(wallet, amount, WalletTransaction.TYPE_WITHDRAWAL, comment)
