# Generated by Django 5.1.4 on 2024-12-11 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0002_record_employees_kc_record_employees_upp_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='in_work',
            field=models.BooleanField(default=1),
            preserve_default=False,
        ),
    ]
