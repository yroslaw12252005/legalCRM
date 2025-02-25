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


class Booking(models.Model):
    client = models.CharField(max_length=100)
    service = models.CharField(max_length=100, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()  # Измененное поле

    def duration_minutes(self):
        """Рассчет длительности в минутах"""
        diff = self.end_time - self.start_time
        return int(diff.total_seconds() // 60)

    def __str__(self):
        return f"{self.client} - {self.service}"