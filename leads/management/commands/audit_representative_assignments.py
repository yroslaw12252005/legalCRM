from django.core.management.base import BaseCommand
from django.db.models import F

from accounts.models import User
from leads.models import Record


UNASSIGNED_VALUES = {
    "",
    "Не прикреплен",
    "Не прикреплён",
    "Не прикреплённ",
    "Не прикрепленн",
}


class Command(BaseCommand):
    help = "Проверяет перенос представителей из employees_REP в representative_user_id."

    def add_arguments(self, parser):
        parser.add_argument(
            "--backfill",
            action="store_true",
            help="Повторно сопоставить пустые ключи по компании и старому username.",
        )

    def handle(self, *args, **options):
        users_by_company_and_username = {
            (company_id, username): user_id
            for user_id, company_id, username in User.objects.values_list(
                "id", "companys_id", "username"
            )
        }

        legacy_records = Record.objects.filter(
            representative_user__isnull=True
        ).only("id", "companys_id", "employees_REP", "representative_user_id")
        pending = []
        for record in legacy_records.iterator(chunk_size=2000):
            username = (record.employees_REP or "").strip()
            if not username or username in UNASSIGNED_VALUES:
                continue
            representative_id = users_by_company_and_username.get(
                (record.companys_id, username)
            )
            if representative_id:
                record.representative_user_id = representative_id
                pending.append(record)

        if options["backfill"] and pending:
            Record.objects.bulk_update(
                pending,
                ["representative_user"],
                batch_size=1000,
            )

        migrated = Record.objects.exclude(representative_user__isnull=True)
        inconsistent_snapshots = migrated.exclude(
            employees_REP=F("representative_user__username")
        )
        unmatched = []
        for record in Record.objects.filter(
            representative_user__isnull=True
        ).only("id", "companys_id", "employees_REP").iterator(chunk_size=2000):
            username = (record.employees_REP or "").strip()
            if username and username not in UNASSIGNED_VALUES:
                unmatched.append(record)

        self.stdout.write(f"Связано по ключу: {migrated.count()}")
        self.stdout.write(f"Можно связать повторным запуском: {len(pending)}")
        self.stdout.write(f"Не найдена учётная запись: {len(unmatched)}")
        self.stdout.write(
            f"Имя-снимок отличается от текущего username: {inconsistent_snapshots.count()}"
        )
        if options["backfill"]:
            self.stdout.write(self.style.SUCCESS(f"Перенесено: {len(pending)}"))
