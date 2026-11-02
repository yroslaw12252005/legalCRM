from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, F

from accounts.models import User
from leads.models import Record


UNASSIGNED_VALUES = (
    None,
    "",
    "Не прикреплен",
    "Не прикреплён",
    "Не прикреплённ",
)


class Command(BaseCommand):
    help = "Проверяет перенос назначенных юристов из employees_UPP в lawyer_id."

    def add_arguments(self, parser):
        parser.add_argument(
            "--backfill",
            action="store_true",
            help="Повторно сопоставить пустые lawyer_id по компании и старому username.",
        )

    def _backfill(self):
        users_by_company_and_username = {
            (company_id, username): user_id
            for user_id, company_id, username in User.objects.exclude(
                companys_id=None
            ).values_list("id", "companys_id", "username")
        }
        updates = []
        updated_count = 0
        records = Record.objects.filter(lawyer__isnull=True).only(
            "id", "companys_id", "employees_UPP", "lawyer_id"
        )
        for record in records.iterator(chunk_size=1000):
            username = (record.employees_UPP or "").strip()
            if username in UNASSIGNED_VALUES:
                continue
            lawyer_id = users_by_company_and_username.get(
                (record.companys_id, username)
            )
            if lawyer_id:
                record.lawyer_id = lawyer_id
                updates.append(record)

            if len(updates) >= 1000:
                Record.objects.bulk_update(updates, ["lawyer"], batch_size=1000)
                updated_count += len(updates)
                updates.clear()

        if updates:
            Record.objects.bulk_update(updates, ["lawyer"], batch_size=1000)
            updated_count += len(updates)
        return updated_count

    def handle(self, *args, **options):
        if options["backfill"]:
            updated = self._backfill()
            self.stdout.write(f"Повторно сопоставлено: {updated}")

        legacy_assigned = Record.objects.exclude(
            employees_UPP__in=UNASSIGNED_VALUES[1:]
        ).exclude(employees_UPP__isnull=True)
        migrated = legacy_assigned.filter(lawyer__isnull=False)
        unmatched = legacy_assigned.filter(lawyer__isnull=True)
        cross_company = Record.objects.filter(lawyer__isnull=False).exclude(
            lawyer__companys_id=F("companys_id")
        )
        snapshot_mismatch = Record.objects.filter(lawyer__isnull=False).exclude(
            employees_UPP=F("lawyer__username")
        )

        self.stdout.write(f"Старых назначений: {legacy_assigned.count()}")
        self.stdout.write(f"Перенесено в lawyer_id: {migrated.count()}")
        self.stdout.write(f"Не сопоставлено: {unmatched.count()}")
        self.stdout.write(f"Связей с юристом другой компании: {cross_company.count()}")
        self.stdout.write(f"Расхождений FK и снимка имени: {snapshot_mismatch.count()}")

        if unmatched.exists():
            self.stdout.write(self.style.WARNING("Несопоставленные назначения:"))
            rows = unmatched.values("companys_id", "employees_UPP").annotate(
                records_count=Count("id")
            ).order_by("companys_id", "employees_UPP")
            for row in rows.iterator():
                self.stdout.write(
                    f"  company={row['companys_id']} "
                    f"username={row['employees_UPP']!r} "
                    f"leads={row['records_count']}"
                )

        if cross_company.exists() or snapshot_mismatch.exists():
            raise CommandError("Обнаружены некорректные связи юристов")

        if unmatched.exists():
            raise CommandError(
                "Не все старые назначения сопоставлены; employees_UPP сохранён для ручной обработки"
            )

        self.stdout.write(self.style.SUCCESS("Все назначения юристов перенесены корректно"))
