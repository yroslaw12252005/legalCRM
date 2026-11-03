import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models

import tilda_integration.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("company", "0003_companys_work_mode"),
        ("felial", "0001_initial"),
        ("leads", "0039_record_lawyer"),
    ]

    operations = [
        migrations.CreateModel(
            name="TildaIntegration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("title", models.CharField(default="Основная форма", max_length=120)),
                ("secret_hash", models.CharField(max_length=128)),
                ("previous_secret_hash", models.CharField(blank=True, default="", max_length=128)),
                ("previous_secret_valid_until", models.DateTimeField(blank=True, null=True)),
                ("field_mapping", models.JSONField(default=tilda_integration.models.default_field_mapping)),
                ("allowed_form_ids", models.JSONField(blank=True, default=list)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_request_at", models.DateTimeField(blank=True, null=True)),
                ("total_received", models.PositiveBigIntegerField(default=0)),
                ("total_processed", models.PositiveBigIntegerField(default=0)),
                ("total_duplicates", models.PositiveBigIntegerField(default=0)),
                ("total_rejected", models.PositiveBigIntegerField(default=0)),
                ("total_auth_failed", models.PositiveBigIntegerField(default=0)),
                ("rate_window_started_at", models.DateTimeField(blank=True, null=True)),
                ("rate_window_count", models.PositiveIntegerField(default=0)),
                ("branch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="tilda_integrations", to="felial.felial")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tilda_integrations", to="company.companys")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_tilda_integrations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="TildaIdempotencyKey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.CharField(max_length=255)),
                ("processed_at", models.DateTimeField(auto_now_add=True)),
                ("integration", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="processed_submissions", to="tilda_integration.tildaintegration")),
                ("lead", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tilda_submissions", to="leads.record")),
            ],
        ),
        migrations.AddConstraint(
            model_name="tildaidempotencykey",
            constraint=models.UniqueConstraint(fields=("integration", "external_id"), name="unique_tilda_submission_per_integration"),
        ),
    ]
