from django.db import models
from accounts.models import User
from leads.models import Record


class Event(models.Model):
    client = models.ForeignKey(Record, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    time = models.DateTimeField()
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Для мультипользовательской системы

    def __str__(self):
        return f"{self.title} ({self.client.name})"
