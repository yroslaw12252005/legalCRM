from django.db import models
from company.models import Companys
from felial.models import Felial

class Record(models.Model):
    name = models.CharField(max_length=50,default=None, null=True)
    phone = models.CharField(max_length=50, default=None, null=True)
    description  = models.CharField(max_length=500, default=None, null=True)
    status = models.CharField(max_length=50,  default='Новая', null=True)
    type = models.CharField(max_length=50,  default='Неизвестен', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    employees_KC = models.CharField(max_length=50,null=True, default="Не прикреплённ")
    employees_UPP = models.CharField(max_length=50,null=True,default="Не прикреплённ")
    employees_REP = models.CharField(max_length=50, null=True, default="Не прикреплённ")
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
    representative = models.BooleanField(default=False)
    doc = models.URLField(max_length=200, null=True)
    def __str__(self):


        return f"{self.name}"

    class Meta:
        ordering = ['-created_at']


class RecordDocument(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="documents")
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)
    s3_key = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.file_name
