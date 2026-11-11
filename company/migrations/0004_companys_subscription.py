from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("company", "0003_companys_work_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="companys",
            name="subscription_expires_at",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="Подписка действует до",
            ),
        ),
        migrations.AddField(
            model_name="companys",
            name="is_subscription_blocked",
            field=models.BooleanField(
                default=False,
                verbose_name="Компания заблокирована",
            ),
        ),
    ]
