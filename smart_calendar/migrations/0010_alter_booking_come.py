# Generated by Django 5.1.4 on 2025-03-25 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smart_calendar', '0009_alter_booking_come'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='come',
            field=models.IntegerField(default=1),
        ),
    ]
