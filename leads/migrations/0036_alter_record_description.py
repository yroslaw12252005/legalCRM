from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0035_record_paid_online"),
    ]

    operations = [
        migrations.AlterField(
            model_name="record",
            name="description",
            field=models.CharField(default=None, max_length=1000, null=True),
        ),
    ]

