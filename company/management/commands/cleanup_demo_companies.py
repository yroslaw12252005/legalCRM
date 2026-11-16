from django.core.management.base import BaseCommand

from company.demo import cleanup_expired_demo_companies


class Command(BaseCommand):
    help = "Удаляет истёкшие изолированные демонстрационные компании"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        deleted = cleanup_expired_demo_companies(limit=max(options["limit"], 1))
        self.stdout.write(self.style.SUCCESS(f"Удалено демокомпаний: {deleted}"))
