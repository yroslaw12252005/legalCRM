from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from felial.models import Felial
from leads.models import Record
from wallet.models import CompanyWallet
from wallet.services import withdraw

from .models import LeadPurchase, LeadStreamSettings, MarketplaceLead


def distribute_marketplace_leads(lead_ids, company):
    lead_ids = sorted(set(lead_ids))
    if not lead_ids:
        raise ValidationError("Выберите хотя бы одну заявку")

    with transaction.atomic():
        leads = list(
            MarketplaceLead.objects.select_for_update()
            .filter(id__in=lead_ids)
            .order_by("id")
        )
        if len(leads) != len(lead_ids):
            raise ValidationError("Одна или несколько заявок не найдены")
        if any(lead.status != MarketplaceLead.STATUS_AVAILABLE for lead in leads):
            raise ValidationError("Одна или несколько заявок уже распределены")

        try:
            stream_settings = LeadStreamSettings.objects.select_for_update().get(company=company)
        except LeadStreamSettings.DoesNotExist:
            raise ValidationError("Компания не настроила параметры потока")
        if not stream_settings.is_enabled:
            raise ValidationError("У выбранной компании поток выключен")
        if stream_settings.lead_price <= 0:
            raise ValidationError("Компания не указала стоимость одного лида")

        total = (stream_settings.lead_price * len(leads)).quantize(Decimal("0.01"))
        if stream_settings.remaining_budget < total:
            raise ValidationError("У компании недостаточно доступного бюджета")

        wallet, _ = CompanyWallet.objects.get_or_create(company=company)
        wallet_operation = withdraw(
            wallet,
            total,
            f"Распределение заявок с биржи: {len(leads)} шт.",
        )
        default_branch = Felial.objects.filter(companys=company).order_by("id").first()
        sold_at = timezone.now()
        purchases = []

        for lead in leads:
            description_parts = [part for part in (lead.note, f"Город: {lead.city}" if lead.city else "") if part]
            crm_record = Record.objects.create(
                name=lead.name,
                phone=lead.phone,
                description="\n".join(description_parts),
                status="Новая",
                type=lead.topic or "Неизвестен",
                where="Биржа заявок",
                companys=company,
                felial=default_branch,
            )
            purchases.append(
                LeadPurchase.objects.create(
                    lead=lead,
                    company=company,
                    price_per_lead=stream_settings.lead_price,
                    wallet_transaction=wallet_operation,
                    crm_record=crm_record,
                )
            )
            lead.status = MarketplaceLead.STATUS_SOLD
            lead.buyer = company
            lead.sold_at = sold_at

        MarketplaceLead.objects.bulk_update(leads, ("status", "buyer", "sold_at"))
        stream_settings.spent_amount += total
        stream_settings.save(update_fields=("spent_amount", "updated_at"))

    return purchases, wallet_operation
