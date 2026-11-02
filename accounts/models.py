from django.db import models
from django.contrib.auth.models import AbstractUser
from company.models import Companys
from felial.models import Felial
from .validators import username_with_spaces_validator


class User(AbstractUser):
    username = models.CharField(
        "имя пользователя",
        max_length=150,
        unique=True,
        help_text=(
            "Не более 150 символов. Разрешены буквы, цифры, пробелы "
            "и знаки @/./+/-/_."
        ),
        validators=[username_with_spaces_validator],
        error_messages={
            "unique": "Пользователь с таким именем уже существует.",
        },
    )
    status = models.CharField(max_length=50)
    companys = models.ForeignKey(
        Companys,
        on_delete=models.CASCADE,
        null = True
    )
    felial = models.ForeignKey(
        Felial,
        on_delete=models.SET_NULL,
        null = True
    )
    percent = models.DecimalField(null=True, max_digits=6, decimal_places=3)
    bet = models.DecimalField(null=True, max_digits=12, decimal_places=6)
    type_zp = models.CharField(null=True, max_length=30)

