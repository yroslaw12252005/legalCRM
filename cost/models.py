from django.db import models

from leads.models import Record
from accounts.models import User
class Surcharge(models.Model):
    cost = models.DecimalField(max_digits=10, decimal_places=0, null=True)
    dat = models.DateTimeField()
    record = models.ForeignKey(Record, on_delete=models.CASCADE, null=True)
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )