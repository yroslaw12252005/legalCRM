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

    @property
    def is_solo(self):
        return self.work_mode == self.MODE_SOLO

    def __str__(self):
        return self.title
