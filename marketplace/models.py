from decimal import Decimal
from datetime import time

from django.core.validators import MinValueValidator
from django.db import models

from company.models import Companys
from leads.models import Record
from wallet.models import WalletTransaction


class LeadStreamSettings(models.Model):
    company = models.OneToOneField(
        Companys,
        on_delete=models.CASCADE,
        related_name="lead_stream_settings",
        verbose_name="Компания",
    )
    work_start = models.TimeField("Начало работы", default=time(9, 0))
    work_end = models.TimeField("Окончание работы", default=time(20, 0))
    budget = models.DecimalField(
        "Бюджет",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    lead_price = models.DecimalField(
        "Стоимость одного лида",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    spent_amount = models.DecimalField(
        "Потрачено",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_enabled = models.BooleanField("Участвовать в потоке", default=False)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Параметры потока"
        verbose_name_plural = "Параметры потоков"
        constraints = [
            models.CheckConstraint(condition=models.Q(budget__gte=0), name="stream_budget_gte_zero"),
            models.CheckConstraint(condition=models.Q(lead_price__gte=0), name="stream_lead_price_gte_zero"),
            models.CheckConstraint(condition=models.Q(spent_amount__gte=0), name="stream_spent_gte_zero"),
        ]

    @property
    def remaining_budget(self):
        return max(self.budget - self.spent_amount, Decimal("0.00"))

    def __str__(self):
        return f"{self.company.title}: {self.lead_price:.2f} ₽ за лид"


class MarketplaceLead(models.Model):
    STATUS_AVAILABLE = "available"
    STATUS_SOLD = "sold"
    STATUS_CHOICES = (
        (STATUS_AVAILABLE, "Не продана"),
        (STATUS_SOLD, "Продана"),
    )

    name = models.CharField("Имя", max_length=100)
    phone = models.CharField("Телефон", max_length=50)
    note = models.TextField("Примечание", blank=True)
    city = models.CharField("Город", max_length=100, blank=True)
    topic = models.CharField("Тематика", max_length=100, blank=True)
    status = models.CharField("Статус", max_length=12, choices=STATUS_CHOICES, default=STATUS_AVAILABLE, db_index=True)
    buyer = models.ForeignKey(
        Companys,
        on_delete=models.PROTECT,
        related_name="marketplace_leads",
        null=True,
        blank=True,
        verbose_name="Компания-покупатель",
    )
    sold_at = models.DateTimeField("Дата продажи", null=True, blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "Заявка на бирже"
        verbose_name_plural = "Заявки на бирже"

    def __str__(self):
        return f"{self.name} — {self.phone}"


class LeadPurchase(models.Model):
    lead = models.OneToOneField(
        MarketplaceLead,
        on_delete=models.PROTECT,
        related_name="purchase",
        verbose_name="Биржевая заявка",
    )
    company = models.ForeignKey(
        Companys,
        on_delete=models.PROTECT,
        related_name="lead_purchases",
        verbose_name="Компания",
    )
    price_per_lead = models.DecimalField("Цена лида", max_digits=12, decimal_places=2)
    wallet_transaction = models.ForeignKey(
        WalletTransaction,
        on_delete=models.PROTECT,
        related_name="lead_purchases",
        verbose_name="Списание",
    )
    crm_record = models.OneToOneField(
        Record,
        on_delete=models.SET_NULL,
        related_name="marketplace_purchase",
        null=True,
        blank=True,
        verbose_name="Заявка в CRM",
    )
    created_at = models.DateTimeField("Дата покупки", auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "Покупка заявки"
        verbose_name_plural = "Покупки заявок"

    def __str__(self):
        return f"{self.company.title}: {self.lead}"
