from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("company", "0004_companys_subscription")]

    operations = [
        migrations.AddField(
            model_name="companys",
            name="is_demo",
            field=models.BooleanField(
                db_index=True,
                default=False,
                verbose_name="Демонстрационная компания",
            ),
        ),
        migrations.AddField(
            model_name="companys",
            name="demo_session_key",
            field=models.UUIDField(
                blank=True,
                default=None,
                editable=False,
                null=True,
                unique=True,
                verbose_name="Ключ демонстрационной сессии",
            ),
        ),
        migrations.AddField(
            model_name="companys",
            name="demo_expires_at",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="Демонстрационная сессия действует до",
            ),
        ),
    ]
