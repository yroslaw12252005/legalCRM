from django.db import models

class Companys(models.Model):
    title = models.CharField(max_length=50)
