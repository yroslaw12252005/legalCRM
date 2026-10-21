import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("leads", "0037_alter_record_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="Contract",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "number",
                    models.CharField(
                        max_length=50,
                        validators=[django.core.validators.RegexValidator("^\\d+$", "Номер договора должен содержать только цифры")],
                        verbose_name="Номер договора",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Сумма договора",
                    ),
                ),
                (
                    "initial_payment",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Сумма, внесённая при заключении",
                    ),
                ),
                ("contract_date", models.DateField(verbose_name="Дата договора")),
                (
                    "record",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contracts",
                        to="leads.record",
                        verbose_name="Клиент",
                    ),
                ),
            ],
            options={"ordering": ["-contract_date", "-id"]},
        ),
        migrations.AddConstraint(
            model_name="contract",
            constraint=models.UniqueConstraint(
                fields=("record", "number"),
                name="unique_contract_number_per_record",
            ),
        ),
        migrations.AddConstraint(
            model_name="contract",
            constraint=models.CheckConstraint(
                condition=models.Q(("initial_payment__lte", models.F("amount"))),
                name="contract_initial_payment_lte_amount",
            ),
        ),
    ]
