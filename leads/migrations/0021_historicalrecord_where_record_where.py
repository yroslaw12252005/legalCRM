# Generated by Django 5.1.4 on 2025-02-11 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0020_historicalrecord_companys_record_companys'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalrecord',
            name='where',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='record',
            name='where',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
