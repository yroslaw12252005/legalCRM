from decimal import Decimal
import datetime

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def create_stream_settings(apps, schema_editor):
    Company = apps.get_model("company", "Companys")
    Settings = apps.get_model("marketplace", "LeadStreamSettings")
    Settings.objects.bulk_create(
        [Settings(company_id=company_id) for company_id in Company.objects.values_list("id", flat=True)],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("company", "0002_remove_companys_telegram_bot"),
        ("leads", "0038_record_client_access_token"),
        ("wallet", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LeadStreamSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("work_start", models.TimeField(default=datetime.time(9, 0), verbose_name="Начало работы")),
                ("work_end", models.TimeField(default=datetime.time(20, 0), verbose_name="Окончание работы")),
                ("budget", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))], verbose_name="Бюджет")),
                ("lead_price", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))], verbose_name="Стоимость одного лида")),
                ("spent_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))], verbose_name="Потрачено")),
                ("is_enabled", models.BooleanField(default=False, verbose_name="Участвовать в потоке")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("company", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="lead_stream_settings", to="company.companys", verbose_name="Компания")),
            ],
            options={"verbose_name": "Параметры потока", "verbose_name_plural": "Параметры потоков"},
        ),
        migrations.CreateModel(
            name="MarketplaceLead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="Имя")),
                ("phone", models.CharField(max_length=50, verbose_name="Телефон")),
                ("note", models.TextField(blank=True, verbose_name="Примечание")),
                ("city", models.CharField(blank=True, max_length=100, verbose_name="Город")),
                ("topic", models.CharField(blank=True, max_length=100, verbose_name="Тематика")),
                ("status", models.CharField(choices=[("available", "Не продана"), ("sold", "Продана")], db_index=True, default="available", max_length=12, verbose_name="Статус")),
                ("sold_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата продажи")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("buyer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="marketplace_leads", to="company.companys", verbose_name="Компания-покупатель")),
            ],
            options={"verbose_name": "Заявка на бирже", "verbose_name_plural": "Заявки на бирже", "ordering": ("-created_at", "-id")},
        ),
        migrations.CreateModel(
            name="LeadPurchase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price_per_lead", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Цена лида")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата покупки")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lead_purchases", to="company.companys", verbose_name="Компания")),
                ("crm_record", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="marketplace_purchase", to="leads.record", verbose_name="Заявка в CRM")),
                ("lead", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="purchase", to="marketplace.marketplacelead", verbose_name="Биржевая заявка")),
                ("wallet_transaction", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lead_purchases", to="wallet.wallettransaction", verbose_name="Списание")),
            ],
            options={"verbose_name": "Покупка заявки", "verbose_name_plural": "Покупки заявок", "ordering": ("-created_at", "-id")},
        ),
        migrations.AddConstraint(model_name="leadstreamsettings", constraint=models.CheckConstraint(condition=models.Q(("budget__gte", 0)), name="stream_budget_gte_zero")),
        migrations.AddConstraint(model_name="leadstreamsettings", constraint=models.CheckConstraint(condition=models.Q(("lead_price__gte", 0)), name="stream_lead_price_gte_zero")),
        migrations.AddConstraint(model_name="leadstreamsettings", constraint=models.CheckConstraint(condition=models.Q(("spent_amount__gte", 0)), name="stream_spent_gte_zero")),
        migrations.RunPython(create_stream_settings, migrations.RunPython.noop),
    ]
