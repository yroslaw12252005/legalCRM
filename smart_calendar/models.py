from django.db import models
from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.models import Record

class Booking(models.Model):
    client = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        null=True
    )
    time = models.CharField(max_length=50, null=True)
    date = models.DateField(null=True)

    employees = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    registrar = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registrar'
    )

    come = models.IntegerField(null=True)
    companys = models.ForeignKey(
        Companys,
        on_delete=models.CASCADE,
        null=True
    )
    felial = models.ForeignKey(
        Felial,
        on_delete=models.SET_NULL,
        null=True

    )
    def duration_minutes(self):
        """Рассчет длительности в минутах"""
        diff = self.end_time - self.start_time
        return int(diff.total_seconds() // 60)

