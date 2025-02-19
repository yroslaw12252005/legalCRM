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

