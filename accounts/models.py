from django.db import models
from django.contrib.auth.models import AbstractUser
from company.models import Companys
from felial.models import Felial


class User(AbstractUser):
    status = models.CharField(max_length=50)
    companys = models.ForeignKey(
        Companys,
        on_delete=models.CASCADE,
        null = True
    )
    felial = models.ForeignKey(
        Felial,
        on_delete=models.SET_NULL,
        null = True
    )
    percent = models.DecimalField(null=True, max_digits=3, decimal_places=3)
    bet = models.DecimalField(null=True, max_digits=6, decimal_places=3)
    type_zp = models.CharField(null=True, max_length=30)

