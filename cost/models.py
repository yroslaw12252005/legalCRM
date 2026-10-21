from django.core.validators import MinValueValidator
from django.db import models

from accounts.models import User
from contract.models import Contract


class Surcharge(models.Model):
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(0)],
    )
    dat = models.DateTimeField()
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="surcharges",
    )
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        ordering = ["dat", "id"]

    def __str__(self):
        return f"Доплата {self.cost} по договору №{self.contract.number}"
