# Generated by Django 4.1.1 on 2024-12-13 13:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        #('coming', '0001_initial'),
        ('leads', '0005_record_reporter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='reporter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coming.coming'),
        ),
    ]
