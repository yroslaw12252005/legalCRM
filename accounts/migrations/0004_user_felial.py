# Generated by Django 5.1.4 on 2025-02-19 12:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_user_companys'),
        ('felial', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='felial',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='felial.felial'),
        ),
    ]
