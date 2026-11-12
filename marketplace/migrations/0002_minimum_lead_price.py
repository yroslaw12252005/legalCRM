from decimal import Decimal

import django.core.validators
from django.db import migrations, models


MIN_LEAD_PRICE = Decimal("300.00")


def normalize_low_lead_prices(apps, schema_editor):
    LeadStreamSettings = apps.get_model("marketplace", "LeadStreamSettings")
    LeadStreamSettings.objects.filter(
        lead_price__gt=0,
        lead_price__lt=MIN_LEAD_PRICE,
    ).update(lead_price=MIN_LEAD_PRICE)


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            normalize_low_lead_prices,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name="leadstreamsettings",
            name="stream_lead_price_gte_zero",
        ),
        migrations.AlterField(
            model_name="leadstreamsettings",
            name="lead_price",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                validators=[
                    django.core.validators.MinValueValidator(
                        MIN_LEAD_PRICE,
                        message="Минимальная стоимость заявки — 300 ₽",
                    )
                ],
                verbose_name="Стоимость одного лида",
            ),
        ),
        migrations.AddConstraint(
            model_name="leadstreamsettings",
            constraint=models.CheckConstraint(
                condition=models.Q(lead_price=0) | models.Q(lead_price__gte=MIN_LEAD_PRICE),
                name="stream_lead_price_zero_or_gte_300",
            ),
        ),
    ]
