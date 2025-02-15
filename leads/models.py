from django.db import models
from company.models import Companys

class Record(models.Model):
    name = models.CharField(max_length=50,default=None, null=True)
    phone = models.CharField(max_length=50, default=None, null=True)
    description  = models.CharField(max_length=500, default=None, null=True)
    status = models.CharField(max_length=50,  default='Новая', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    employees_KC = models.CharField(max_length=50, default="Не прикреплен")
    employees_UPP = models.CharField(max_length=50,default="Не прикреплен")
    where = models.CharField(max_length=50, null=True)
    companys = models.ForeignKey(
        Companys,
        on_delete=models.CASCADE,
         default="Не прикреплен"
    )
    in_work = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ['-created_at']
