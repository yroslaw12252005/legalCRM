from django.db import migrations


OLD_STATUS = "\u042e\u0440\u0438\u0441\u0442 \u043f\u0438\u0440\u0432\u0438\u0447\u043d\u0438\u043a"
NEW_STATUS = "Юрист первичник"


def rename_primary_lawyer_status(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(status=OLD_STATUS).update(status=NEW_STATUS)


def restore_primary_lawyer_status(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(status=NEW_STATUS).update(status=OLD_STATUS)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0012_user_onboarding"),
    ]

    operations = [
        migrations.RunPython(
            rename_primary_lawyer_status,
            restore_primary_lawyer_status,
        ),
    ]
