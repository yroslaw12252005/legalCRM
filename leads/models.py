from django.db import models


class Record(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    description  = models.CharField(max_length=500)
    status = models.CharField(max_length=50,  default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    employees_KC = models.CharField(max_length=50, default="Не прикреплен")
    employees_UPP = models.CharField(max_length=50,default="Не прикреплен")
    in_work = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"
