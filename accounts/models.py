from django.db import models
from django.contrib.auth.models import AbstractUser
from company.models import Companys


class User(AbstractUser):
    status = models.CharField(max_length=50)
    companys = models.ForeignKey(
        Companys,
        on_delete=models.CASCADE
    )
# Create your models here.
