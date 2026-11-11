from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from company.models import Companys
from felial.models import Felial
from .validators import username_with_spaces_validator


class User(AbstractUser):
    SALARY_PERCENT = "Процент"
    SALARY_FIXED = "Оклад"
    SALARY_COMBINED = "Оклад + Процент"
    SALARY_TYPE_CHOICES = (
        (SALARY_PERCENT, "Процент"),
        (SALARY_FIXED, "Оклад"),
        (SALARY_COMBINED, "Оклад + процент"),
    )
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
    percent = models.DecimalField(
        "Процент",
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    bet = models.DecimalField(
        "Месячный оклад",
        null=True,
        blank=True,
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    type_zp = models.CharField(
        "Тип ЗП",
        null=True,
        blank=True,
        max_length=30,
        choices=SALARY_TYPE_CHOICES,
    )
    is_account_blocked = models.BooleanField(
        "Учётная запись заблокирована",
        default=False,
    )

