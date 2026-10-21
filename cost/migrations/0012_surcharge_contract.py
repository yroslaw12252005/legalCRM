from datetime import date

import django.db.models.deletion
import django.core.validators
from django.db import migrations, models


def move_surcharges_to_contracts(apps, schema_editor):
    Record = apps.get_model("leads", "Record")
    Contract = apps.get_model("contract", "Contract")
    Surcharge = apps.get_model("cost", "Surcharge")

    record_ids = set(
        Record.objects.exclude(cost__isnull=True).values_list("id", flat=True)
    )
    record_ids.update(
        Surcharge.objects.exclude(record_id__isnull=True).values_list("record_id", flat=True)
    )

    for record in Record.objects.filter(id__in=record_ids).iterator():
        contract = Contract.objects.create(
            record_id=record.id,
            number="0",
            amount=record.cost or 0,
            initial_payment=0,
            contract_date=getattr(record, "created_at", None).date() if getattr(record, "created_at", None) else date.today(),
        )
        Surcharge.objects.filter(record_id=record.id).update(contract_id=contract.id)


class Migration(migrations.Migration):
    dependencies = [
        ("contract", "0001_initial"),
        ("cost", "0011_surcharge_responsible"),
    ]

    operations = [
        migrations.AddField(
            model_name="surcharge",
            name="contract",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="surcharges",
                to="contract.contract",
            ),
        ),
        migrations.RunPython(move_surcharges_to_contracts, migrations.RunPython.noop),
        migrations.RemoveField(model_name="surcharge", name="record"),
        migrations.AlterField(
            model_name="surcharge",
            name="contract",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="surcharges",
                to="contract.contract",
            ),
        ),
        migrations.AlterField(
            model_name="surcharge",
            name="cost",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=12,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AlterModelOptions(
            name="surcharge",
            options={"ordering": ["dat", "id"]},
        ),
    ]
