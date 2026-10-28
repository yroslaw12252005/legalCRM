from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from company.models import Companys


class CompanyWallet(models.Model):
    company = models.OneToOneField(
        Companys,
        on_delete=models.CASCADE,
        related_name="wallet",
        verbose_name="Компания",
    )
    balance = models.DecimalField(
        "Баланс",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Кошелёк компании"
        verbose_name_plural = "Кошельки компаний"

    def __str__(self):
        return f"{self.company.title}: {self.balance:.2f} ₽"


class WalletTransaction(models.Model):
    TYPE_DEPOSIT = "deposit"
    TYPE_WITHDRAWAL = "withdrawal"
    TYPE_CHOICES = (
        (TYPE_DEPOSIT, "Пополнение"),
        (TYPE_WITHDRAWAL, "Списание"),
    )

    wallet = models.ForeignKey(
        CompanyWallet,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Кошелёк",
    )
    operation_type = models.CharField("Тип операции", max_length=12, choices=TYPE_CHOICES)
    amount = models.DecimalField(
        "Сумма",
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    balance_after = models.DecimalField("Баланс после операции", max_digits=14, decimal_places=2)
    comment = models.CharField("Комментарий", max_length=255, blank=True)
    created_at = models.DateTimeField("Дата операции", auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "Денежная операция"
        verbose_name_plural = "Денежные операции"

    def __str__(self):
        return f"{self.get_operation_type_display()}: {self.amount:.2f} ₽"
