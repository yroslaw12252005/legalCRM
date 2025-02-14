from django.db import models

from leads.models import Record

class Cost(models.Model):
    cost = models.DecimalField(max_digits=10, decimal_places=0, null=True)
    record = models.OneToOneField(Record, on_delete=models.CASCADE, null=True)

class Surcharge(models.Model):
    surcharge = models.DecimalField(max_digits=10, decimal_places=0, null=True)
    date = models.DateTimeField(auto_now_add=True)
    record = models.ForeignKey(Record, on_delete=models.CASCADE, null=True)