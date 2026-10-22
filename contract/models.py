from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from leads.models import Record


class Contract(models.Model):
    number = models.CharField(
        "Номер договора",
        max_length=50,
        validators=[RegexValidator(r"^\d+$", "Номер договора должен содержать только цифры")],
    )
    amount = models.DecimalField(
        "Сумма договора",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    initial_payment = models.DecimalField(
        "Сумма, внесённая при заключении",
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    contract_date = models.DateField("Дата договора")
    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        related_name="contracts",
        verbose_name="Клиент",
    )

    class Meta:
        ordering = ["-contract_date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["record", "number"],
                name="unique_contract_number_per_record",
            ),
            models.CheckConstraint(
                condition=models.Q(initial_payment__lte=models.F("amount")),
                name="contract_initial_payment_lte_amount",
            ),
        ]

    def __str__(self):
        return f"Договор №{self.number}"

    @property
    def remaining_amount(self):
        return self.amount - self.initial_payment

