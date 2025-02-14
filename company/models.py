from django.db import models

class Companys(models.Model):
    title = models.CharField(max_length=50)
    telegram_bot = models.CharField(max_length=50)