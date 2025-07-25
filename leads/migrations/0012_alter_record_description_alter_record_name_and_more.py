# Generated by Django 5.1.4 on 2024-12-27 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0011_alter_record_description_alter_record_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='description',
            field=models.CharField(default=None, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='record',
            name='name',
            field=models.CharField(default=None, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='record',
            name='phone',
            field=models.CharField(default=None, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='record',
            name='status',
            field=models.CharField(default='Новая', max_length=50, null=True),
        ),
    ]
