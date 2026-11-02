from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


UNASSIGNED_VALUES = {
    None,
    "",
    "Не прикреплен",
    "Не прикреплён",
    "Не прикреплённ",
}


def populate_record_lawyers(apps, schema_editor):
    Record = apps.get_model("leads", "Record")
    User = apps.get_model("accounts", "User")

    users_by_company_and_username = {
        (company_id, username): user_id
        for user_id, company_id, username in User.objects.exclude(companys_id=None).values_list(
            "id", "companys_id", "username"
        )
    }

    pending_updates = []
    records = Record.objects.filter(lawyer__isnull=True).only(
        "id", "companys_id", "employees_UPP", "lawyer_id"
    )
    for record in records.iterator(chunk_size=1000):
        legacy_username = (record.employees_UPP or "").strip()
        if legacy_username in UNASSIGNED_VALUES:
            continue

        lawyer_id = users_by_company_and_username.get(
            (record.companys_id, legacy_username)
        )
        if lawyer_id:
            record.lawyer_id = lawyer_id
            pending_updates.append(record)

        if len(pending_updates) >= 1000:
            Record.objects.bulk_update(pending_updates, ["lawyer"])
            pending_updates.clear()

    if pending_updates:
        Record.objects.bulk_update(pending_updates, ["lawyer"])


def clear_record_lawyers(apps, schema_editor):
    # The legacy employees_UPP snapshot is intentionally left untouched.
    apps.get_model("leads", "Record").objects.update(lawyer=None)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_alter_user_bet_alter_user_percent"),
        ("leads", "0038_record_client_access_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="record",
            name="lawyer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="assigned_leads_as_lawyer",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Прикреплённый юрист",
            ),
        ),
        migrations.RunPython(populate_record_lawyers, clear_record_lawyers),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="record",
                    name="employees_KC",
                    field=models.CharField(
                        default="Не прикреплён",
                        max_length=50,
                        null=True,
                    ),
                ),
                migrations.AlterField(
                    model_name="record",
                    name="employees_REP",
                    field=models.CharField(
                        default="Не прикреплён",
                        max_length=50,
                        null=True,
                    ),
                ),
                migrations.AlterField(
                    model_name="record",
                    name="employees_UPP",
                    field=models.CharField(
                        default="Не прикреплён",
                        max_length=50,
                        null=True,
                    ),
                ),
            ],
        ),
    ]
