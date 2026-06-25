from django.db import models

from company.models import Companys


class CallRecording(models.Model):
    companys = models.ForeignKey(Companys, on_delete=models.CASCADE, related_name="call_recordings")
    phone = models.CharField(max_length=50, db_index=True)
    operator_phone = models.CharField(max_length=50, blank=True, default="")
    external_id = models.CharField(max_length=100, unique=True)
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)
    s3_key = models.CharField(max_length=500, unique=True)
    call_started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-call_started_at", "-created_at"]

    def __str__(self):
        return f"{self.phone} ({self.external_id})"

