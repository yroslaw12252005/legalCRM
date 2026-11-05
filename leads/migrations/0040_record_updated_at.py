from django.db import migrations, models
from django.db.models import F


def populate_updated_at(apps, schema_editor):
    Record = apps.get_model("leads", "Record")
    Record.objects.update(updated_at=F("created_at"))


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0039_record_lawyer"),
    ]

    operations = [
        migrations.AddField(
            model_name="record",
            name="updated_at",
            field=models.DateTimeField(db_index=True, null=True),
        ),
        migrations.RunPython(populate_updated_at, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="record",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterModelOptions(
            name="record",
            options={"ordering": ["-updated_at", "-created_at", "-id"]},
        ),
    ]
