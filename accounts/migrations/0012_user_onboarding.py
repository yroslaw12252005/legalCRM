from django.db import migrations, models


def mark_existing_users_as_onboarded(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.update(onboarding_version=1)


def reset_onboarding_version(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.update(onboarding_version=0)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_user_is_account_blocked"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="onboarding_completed_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Обучение завершено",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="onboarding_deferred_until",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Обучение отложено до",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="onboarding_step",
            field=models.PositiveSmallIntegerField(
                default=0,
                verbose_name="Текущий шаг обучения",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="onboarding_version",
            field=models.PositiveSmallIntegerField(
                default=0,
                verbose_name="Пройденная версия обучения",
            ),
        ),
        migrations.RunPython(
            mark_existing_users_as_onboarded,
            reset_onboarding_version,
        ),
    ]
