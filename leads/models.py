import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone

from company.models import Companys
from felial.models import Felial


class RecordQuerySet(models.QuerySet):
    def update(self, **kwargs):
        kwargs.setdefault("updated_at", timezone.now())
        return super().update(**kwargs)


class Record(models.Model):
    objects = RecordQuerySet.as_manager()
    client_access_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=50, default=None, null=True)
    phone = models.CharField(max_length=50, default=None, null=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    social_links = models.TextField(default="", blank=True)
    description = models.CharField(max_length=5000, default=None, null=True)
    work_comment_kc = models.TextField(default="", blank=True)
    work_comment = models.TextField(default="", blank=True)
    work_comment_op = models.TextField(default="", blank=True)
    status = models.CharField(max_length=50, default="Новая", null=True)
    type = models.CharField(max_length=50, default="Неизвестен", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    employees_KC = models.CharField(max_length=50, null=True, default="Не прикреплён")
    employees_UPP = models.CharField(max_length=50, null=True, default="Не прикреплён")
    lawyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assigned_leads_as_lawyer",
        verbose_name="Прикреплённый юрист",
    )
    employees_REP = models.CharField(max_length=50, null=True, default="Не прикреплён")
    representative_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assigned_leads_as_representative",
        verbose_name="Прикреплённый представитель",
    )
    where = models.CharField(max_length=50, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=0, null=True)
    companys = models.ForeignKey(Companys, on_delete=models.CASCADE)
    felial = models.ForeignKey(Felial, on_delete=models.SET_NULL, null=True)
    in_work = models.BooleanField(default=False)
    representative = models.BooleanField(default=False)
    doc = models.URLField(max_length=200, null=True)
    paid_online = models.PositiveSmallIntegerField(default=0, verbose_name="Paid Online")

    def _assign_solo_lawyer(self):
        if self.lawyer_id or not self.companys_id:
            return
        company = self.companys
        if not company.is_solo:
            return

        UserModel = self._meta.get_field("lawyer").remote_field.model
        lawyer = UserModel.objects.filter(
            companys_id=self.companys_id,
            is_active=True,
            status="Администратор",
        ).order_by("id").first()
        if lawyer:
            self.lawyer = lawyer
            self.employees_UPP = lawyer.username

    def save(self, *args, **kwargs):
        if self._state.adding:
            self._assign_solo_lawyer()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"updated_at"}
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    @property
    def lawyer_display_name(self):
        """Return the FK lawyer name, falling back to the legacy snapshot."""
        if self.lawyer_id:
            return self.lawyer.username
        return self.employees_UPP or "Не прикреплён"

    def is_assigned_to_lawyer(self, user):
        """Support both migrated and not-yet-migrated lawyer assignments."""
        if not user or not getattr(user, "pk", None):
            return False
        if self.lawyer_id:
            return self.lawyer_id == user.pk
        return self.employees_UPP == user.username

    @property
    def representative_display_name(self):
        """Return the FK representative name, falling back to the legacy snapshot."""
        if self.representative_user_id:
            return self.representative_user.username
        return self.employees_REP or "Не прикреплён"

    def is_assigned_to_representative(self, user):
        """Support both migrated and unmatched legacy representative assignments."""
        if not user or not getattr(user, "pk", None):
            return False
        if self.representative_user_id:
            return self.representative_user_id == user.pk
        return self.employees_REP == user.username

    class Meta:
        ordering = ["-updated_at", "-created_at", "-id"]


class RecordDocument(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="documents")
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)
    s3_key = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.file_name

    @property
    def extension(self):
        return Path(self.file_name).suffix.lstrip(".").upper() or "FILE"
