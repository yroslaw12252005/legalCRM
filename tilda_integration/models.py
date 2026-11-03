import uuid

from django.conf import settings
from django.db import models

from company.models import Companys
from felial.models import Felial
from leads.models import Record


def default_field_mapping():
    return {
        "name": ["name", "fullname", "fio", "your_name", "имя", "фио"],
        "phone": ["phone", "tel", "telephone", "mobile", "custom_phone", "телефон"],
        "email": ["email", "mail", "почта"],
        "comment": ["comment", "comments", "message", "textarea", "question", "комментарий"],
    }


class TildaIntegration(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    company = models.ForeignKey(
        Companys,
        on_delete=models.CASCADE,
        related_name="tilda_integrations",
    )
    branch = models.ForeignKey(
        Felial,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tilda_integrations",
    )
    title = models.CharField(max_length=120, default="Основная форма")
    secret_hash = models.CharField(max_length=128)
    previous_secret_hash = models.CharField(max_length=128, blank=True, default="")
    previous_secret_valid_until = models.DateTimeField(null=True, blank=True)
    field_mapping = models.JSONField(default=default_field_mapping)
    allowed_form_ids = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tilda_integrations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_request_at = models.DateTimeField(null=True, blank=True)
    total_received = models.PositiveBigIntegerField(default=0)
    total_processed = models.PositiveBigIntegerField(default=0)
    total_duplicates = models.PositiveBigIntegerField(default=0)
    total_rejected = models.PositiveBigIntegerField(default=0)
    total_auth_failed = models.PositiveBigIntegerField(default=0)
    rate_window_started_at = models.DateTimeField(null=True, blank=True)
    rate_window_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company}: {self.title}"


class TildaIdempotencyKey(models.Model):
    """Minimal idempotency registry; raw webhook requests are intentionally not stored."""

    integration = models.ForeignKey(
        TildaIntegration,
        on_delete=models.CASCADE,
        related_name="processed_submissions",
    )
    external_id = models.CharField(max_length=255)
    lead = models.ForeignKey(
        Record,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tilda_submissions",
    )
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["integration", "external_id"],
                name="unique_tilda_submission_per_integration",
            )
        ]

    def __str__(self):
        return f"{self.integration_id}: {self.external_id}"
