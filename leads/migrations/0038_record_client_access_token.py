import uuid

from django.db import migrations, models


def populate_client_access_tokens(apps, schema_editor):
    Record = apps.get_model("leads", "Record")
    batch = []
    queryset = Record.objects.filter(client_access_token__isnull=True).only("pk")

    for record in queryset.iterator(chunk_size=500):
        record.client_access_token = uuid.uuid4()
        batch.append(record)
        if len(batch) == 500:
            Record.objects.bulk_update(batch, ["client_access_token"], batch_size=500)
            batch.clear()

    if batch:
        Record.objects.bulk_update(batch, ["client_access_token"], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0037_alter_record_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="record",
            name="client_access_token",
            field=models.UUIDField(editable=False, null=True, unique=True),
        ),
        migrations.RunPython(populate_client_access_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="record",
            name="client_access_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
