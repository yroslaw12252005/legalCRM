from django.db import migrations, models


def synchronize_account_blocks(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(companys__is_subscription_blocked=True).update(
        is_account_blocked=True
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_salary_settings"),
        ("company", "0004_companys_subscription"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_account_blocked",
            field=models.BooleanField(
                default=False,
                verbose_name="Учётная запись заблокирована",
            ),
        ),
        migrations.RunPython(
            synchronize_account_blocks,
            migrations.RunPython.noop,
        ),
    ]
