# Generated by Django 5.1.4 on 2025-03-11 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_user_bet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='bet',
            field=models.DecimalField(decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='percent',
            field=models.DecimalField(decimal_places=3, max_digits=5, null=True),
        ),
    ]
