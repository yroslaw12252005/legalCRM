from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def normalize_salary_settings(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    type_mapping = {
        "Ставка": "Оклад",
        "Процент + Ставка": "Оклад + Процент",
        "Процент+Ставка": "Оклад + Процент",
        "Оклад+Процент": "Оклад + Процент",
    }
    for user in User.objects.all().iterator():
        update_fields = []
        normalized_type = type_mapping.get(user.type_zp)
        if normalized_type:
            user.type_zp = normalized_type
            update_fields.append("type_zp")
        if user.percent is not None and Decimal("0") <= user.percent <= Decimal("1"):
            user.percent *= Decimal("100")
            update_fields.append("percent")
        if update_fields:
            user.save(update_fields=update_fields)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0009_alter_user_username")]

    operations = [
        migrations.RunPython(normalize_salary_settings, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="percent",
            field=models.DecimalField(
                "Процент",
                null=True,
                blank=True,
                max_digits=6,
                decimal_places=3,
                validators=[MinValueValidator(0), MaxValueValidator(100)],
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="bet",
            field=models.DecimalField(
                "Месячный оклад",
                null=True,
                blank=True,
                max_digits=12,
                decimal_places=2,
                validators=[MinValueValidator(0)],
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="type_zp",
            field=models.CharField(
                "Тип ЗП",
                null=True,
                blank=True,
                max_length=30,
                choices=(
                    ("Процент", "Процент"),
                    ("Оклад", "Оклад"),
                    ("Оклад + Процент", "Оклад + процент"),
                ),
            ),
        ),
    ]
