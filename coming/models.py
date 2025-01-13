from django.db import models
from leads.models import Record

class Coming(models.Model):
    date = models.DateTimeField()
    come = models.BooleanField(default=False)
    lead = models.OneToOneField(Record, on_delete=models.CASCADE, default=None,
                                null=True,
                                blank=True, related_name='coming')
