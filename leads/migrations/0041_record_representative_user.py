from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


UNASSIGNED_VALUES = {
    "",
    "Не прикреплен",
    "Не прикреплён",
    "Не прикреплённ",
    "Не прикрепленн",
}


def backfill_representative_users(apps, schema_editor):
    Record = apps.get_model("leads", "Record")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

    users_by_company_and_username = {
        (company_id, username): user_id
        for user_id, company_id, username in User.objects.exclude(
            username__isnull=True
        ).values_list("id", "companys_id", "username")
    }

    pending = []
    records = Record.objects.filter(representative_user__isnull=True).only(
        "id", "companys_id", "employees_REP", "representative_user_id"
    )
    for record in records.iterator(chunk_size=2000):
        legacy_username = (record.employees_REP or "").strip()
        if not legacy_username or legacy_username in UNASSIGNED_VALUES:
            continue
        representative_id = users_by_company_and_username.get(
            (record.companys_id, legacy_username)
        )
        if representative_id:
            record.representative_user_id = representative_id
            pending.append(record)

    if pending:
        Record.objects.bulk_update(
            pending,
            ["representative_user"],
            batch_size=1000,
        )


def clear_representative_users(apps, schema_editor):
    apps.get_model("leads", "Record").objects.update(representative_user=None)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_user_is_account_blocked"),
        ("leads", "0040_record_updated_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="record",
            name="representative_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="assigned_leads_as_representative",
                to="accounts.user",
                verbose_name="Прикреплённый представитель",
            ),
        ),
        migrations.RunPython(
            backfill_representative_users,
            clear_representative_users,
        ),
    ]
