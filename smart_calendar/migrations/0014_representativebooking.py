from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("company", "0001_initial"),
        ("felial", "0001_initial"),
        ("leads", "0031_recorddocument"),
        ("smart_calendar", "0013_alter_booking_come"),
    ]

    operations = [
        migrations.CreateModel(
            name="RepresentativeBooking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("destination", models.CharField(max_length=255)),
                ("time", models.CharField(max_length=50, null=True)),
                ("date", models.DateField(null=True)),
                ("client", models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="leads.record")),
                ("companys", models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="company.companys")),
                ("felial", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="felial.felial")),
                (
                    "registrar",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="representative_booking_registrar",
                        to="accounts.user",
                    ),
                ),
                (
                    "representative",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="representative_bookings",
                        to="accounts.user",
                    ),
                ),
            ],
        ),
    ]
