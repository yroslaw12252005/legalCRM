from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    status = models.CharField(max_length=50)
# Create your models here.
