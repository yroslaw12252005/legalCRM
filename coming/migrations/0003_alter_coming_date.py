# Generated by Django 5.1.4 on 2024-12-16 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coming', '0002_coming_lead'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coming',
            name='date',
            field=models.DateTimeField(),
        ),
    ]
