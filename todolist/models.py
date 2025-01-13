from django.db import models
from accounts.models import User

class ToDoList(models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    time = models.DateTimeField()
    made = models.BooleanField(default=False)
    priority = models.CharField(max_length=50)
    category = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)