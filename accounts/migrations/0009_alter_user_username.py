from django.db import migrations, models

import accounts.validators


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_alter_user_bet_alter_user_percent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(
                error_messages={
                    "unique": "Пользователь с таким именем уже существует.",
                },
                help_text=(
                    "Не более 150 символов. Разрешены буквы, цифры, пробелы "
                    "и знаки @/./+/-/_."
                ),
                max_length=150,
                unique=True,
                validators=[accounts.validators.username_with_spaces_validator],
                verbose_name="имя пользователя",
            ),
        ),
    ]
