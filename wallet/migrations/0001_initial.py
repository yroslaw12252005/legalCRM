from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def create_company_wallets(apps, schema_editor):
    Company = apps.get_model("company", "Companys")
    Wallet = apps.get_model("wallet", "CompanyWallet")
    Wallet.objects.bulk_create(
        [Wallet(company_id=company_id) for company_id in Company.objects.values_list("id", flat=True)],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [("company", "0002_remove_companys_telegram_bot")]

    operations = [
        migrations.CreateModel(
            name="CompanyWallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("balance", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))], verbose_name="Баланс")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлён")),
                ("company", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="wallet", to="company.companys", verbose_name="Компания")),
            ],
            options={"verbose_name": "Кошелёк компании", "verbose_name_plural": "Кошельки компаний"},
        ),
        migrations.CreateModel(
            name="WalletTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("operation_type", models.CharField(choices=[("deposit", "Пополнение"), ("withdrawal", "Списание")], max_length=12, verbose_name="Тип операции")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))], verbose_name="Сумма")),
                ("balance_after", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Баланс после операции")),
                ("comment", models.CharField(blank=True, max_length=255, verbose_name="Комментарий")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата операции")),
                ("wallet", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to="wallet.companywallet", verbose_name="Кошелёк")),
            ],
            options={"verbose_name": "Денежная операция", "verbose_name_plural": "Денежные операции", "ordering": ("-created_at", "-id")},
        ),
        migrations.RunPython(create_company_wallets, migrations.RunPython.noop),
    ]
