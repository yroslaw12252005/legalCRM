from django.db import models
from company.models import Companys
from felial.models import Felial

class Record(models.Model):
    name = models.CharField(max_length=50,default=None, null=True)
    phone = models.CharField(max_length=50, default=None, null=True)
    description  = models.CharField(max_length=500, default=None, null=True)
    status = models.CharField(max_length=50,  default='Новая', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    employees_KC = models.CharField(max_length=50,null=True, default="Не прикреплённ")
    employees_UPP = models.CharField(max_length=50,null=True,default="Не прикреплённ")
    where = models.CharField(max_length=50, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=0, null=True)
    companys = models.ForeignKey(
        Companys,
        on_delete=models.CASCADE
    )
    felial = models.ForeignKey(
        Felial,
        on_delete=models.SET_NULL,
        null = True
    )
    in_work = models.BooleanField(default=False)
    doc = models.URLField(max_length=200, null=True)
    def __str__(self):


        return f"{self.name}"

    class Meta:
        ordering = ['-created_at']
