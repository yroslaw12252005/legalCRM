from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models

from legalCRM.text_normalizer import normalize_instance_text_fields


class Command(BaseCommand):
    help = "Исправляет кракозябры в текстовых полях всех моделей проекта."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать, сколько записей будет исправлено, без сохранения.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        total_objects = 0
        total_updated = 0

        for model in apps.get_models():
            model_label = f"{model._meta.app_label}.{model.__name__}"
            text_fields = [
                field.name
                for field in model._meta.fields
                if isinstance(field, (models.CharField, models.TextField))
            ]
            if not text_fields:
                continue

            model_checked = 0
            model_updated = 0
            queryset = model.objects.all().iterator(chunk_size=500)
            for obj in queryset:
                model_checked += 1
                changed_fields = normalize_instance_text_fields(obj)
                if not changed_fields:
                    continue
                model_updated += 1
                if not dry_run:
                    obj.save(update_fields=changed_fields)

            if model_checked:
                self.stdout.write(
                    f"{model_label}: checked={model_checked}, updated={model_updated}"
                )
                total_objects += model_checked
                total_updated += model_updated

        mode = "DRY-RUN" if dry_run else "APPLY"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode} done: checked={total_objects}, updated={total_updated}"
            )
        )
