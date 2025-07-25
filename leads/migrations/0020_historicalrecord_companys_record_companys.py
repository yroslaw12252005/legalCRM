# Generated by Django 5.1.4 on 2025-01-22 19:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
        ('leads', '0019_remove_historicalrecord_cost_remove_record_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalrecord',
            name='companys',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='company.companys'),
        ),
        migrations.AddField(
            model_name='record',
            name='companys',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='company.companys'),
            preserve_default=False,
        ),
    ]
