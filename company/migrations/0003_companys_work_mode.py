from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("company", "0002_remove_companys_telegram_bot"),
    ]

    operations = [
        migrations.AddField(
            model_name="companys",
            name="work_mode",
            field=models.CharField(
                choices=[
                    ("solo", "Самостоятельная работа"),
                    ("team", "Компания с отделами"),
                ],
                default="team",
                max_length=10,
                verbose_name="Формат работы",
            ),
        ),
    ]
