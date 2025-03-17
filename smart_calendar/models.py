from django.db import models
from accounts.models import User
from company.models import Companys
from felial.models import Felial
class Booking(models.Model):
    client = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    employees = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
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

    def __str__(self):
        return f"{self.client}"