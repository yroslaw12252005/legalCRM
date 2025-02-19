from django.db import models
from company.models import Companys

class Felial(models.Model):
    cites = models.CharField(max_length=50, default=None, null=True)
    title = models.CharField(max_length=50, default=None, null=True)
    companys = models.ForeignKey(
        Companys,
        on_delete=models.CASCADE,
        null = True
    )

    def __str__(self):
        return f"{self.cites} - {self.title}"

