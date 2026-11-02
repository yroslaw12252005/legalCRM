from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.db.models.functions import Lower


class Command(BaseCommand):
    help = "Проверяет активные учётки перед включением авторизации по email."

    def handle(self, *args, **options):
        User = get_user_model()
        active_users = User.objects.filter(is_active=True)
        missing_email = active_users.filter(email__exact="") | active_users.filter(email__isnull=True)
        duplicate_emails = (
            active_users.exclude(email__exact="")
            .exclude(email__isnull=True)
            .annotate(normalized_email=Lower("email"))
            .values("normalized_email")
            .annotate(users_count=Count("id"))
            .filter(users_count__gt=1)
            .order_by("normalized_email")
        )

        self.stdout.write(f"Активных пользователей: {active_users.count()}")
        self.stdout.write(f"Без email: {missing_email.count()}")
        self.stdout.write(f"Повторяющихся email: {duplicate_emails.count()}")

        if missing_email.exists():
            self.stdout.write(self.style.WARNING("Активные учётки без email:"))
            for user in missing_email.only("id", "username").order_by("id").iterator():
                self.stdout.write(f"  id={user.id} username={user.username!r}")

        if duplicate_emails.exists():
            self.stdout.write(self.style.WARNING("Неоднозначные email:"))
            for row in duplicate_emails.iterator():
                self.stdout.write(
                    f"  email={row['normalized_email']!r} users={row['users_count']}"
                )

        if missing_email.exists():
            raise CommandError("Не все активные учётки готовы к авторизации по email")

        if duplicate_emails.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Вход возможен по сочетанию email и уникального пароля; дубли рекомендуется устранить"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("Все активные учётки готовы к входу по email"))
