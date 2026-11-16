from django.db import models

class Companys(models.Model):
    MODE_SOLO = "solo"
    MODE_TEAM = "team"
    MODE_CHOICES = (
        (MODE_SOLO, "Самостоятельная работа"),
        (MODE_TEAM, "Компания с отделами"),
    )

    title = models.CharField(max_length=50)
    work_mode = models.CharField(
        max_length=10,
        choices=MODE_CHOICES,
        default=MODE_TEAM,
        verbose_name="Формат работы",
    )
    subscription_expires_at = models.DateField(
        null=True,
        blank=True,
        verbose_name="Подписка действует до",
    )
    is_subscription_blocked = models.BooleanField(
        default=False,
        verbose_name="Компания заблокирована",
    )
    is_demo = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Демонстрационная компания",
    )
    demo_session_key = models.UUIDField(
        default=None,
        null=True,
        blank=True,
        unique=True,
        editable=False,
        verbose_name="Ключ демонстрационной сессии",
    )
    demo_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Демонстрационная сессия действует до",
    )

    @property
    def is_solo(self):
        return self.work_mode == self.MODE_SOLO

    def __str__(self):
        return self.title
