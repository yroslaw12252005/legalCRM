# Generated by Django 5.1.4 on 2025-03-20 18:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smart_calendar', '0005_remove_booking_end_time_remove_booking_start_time_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='registering',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='registering', to=settings.AUTH_USER_MODEL),
        ),
    ]
