from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("company", "0002_remove_companys_telegram_bot"),
    ]

    operations = [
        migrations.CreateModel(
            name="CallRecording",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(db_index=True, max_length=50)),
                ("operator_phone", models.CharField(blank=True, default="", max_length=50)),
                ("external_id", models.CharField(max_length=100, unique=True)),
                ("file_name", models.CharField(max_length=255)),
                ("file_url", models.URLField(max_length=500)),
                ("s3_key", models.CharField(max_length=500, unique=True)),
                ("call_started_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "companys",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="call_recordings", to="company.companys"),
                ),
            ],
            options={"ordering": ["-call_started_at", "-created_at"]},
        ),
    ]

