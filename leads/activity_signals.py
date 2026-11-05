from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from contract.models import Contract
from cost.models import Surcharge
from marketplace.models import LeadPurchase
from smart_calendar.models import Booking, CallBooking, RepresentativeBooking

from .models import Record, RecordDocument


def touch_record(record_id):
    if record_id:
        Record.objects.filter(pk=record_id).update(updated_at=timezone.now())


@receiver([post_save, post_delete], sender=RecordDocument)
def touch_record_for_document(sender, instance, **kwargs):
    touch_record(instance.record_id)


@receiver([post_save, post_delete], sender=Contract)
def touch_record_for_contract(sender, instance, **kwargs):
    touch_record(instance.record_id)


@receiver(post_save, sender=Surcharge)
def touch_record_for_saved_surcharge(sender, instance, **kwargs):
    record_id = Contract.objects.filter(pk=instance.contract_id).values_list("record_id", flat=True).first()
    touch_record(record_id)


@receiver(pre_delete, sender=Surcharge)
def touch_record_for_deleted_surcharge(sender, instance, **kwargs):
    record_id = Contract.objects.filter(pk=instance.contract_id).values_list("record_id", flat=True).first()
    touch_record(record_id)


@receiver([post_save, post_delete], sender=Booking)
@receiver([post_save, post_delete], sender=CallBooking)
@receiver([post_save, post_delete], sender=RepresentativeBooking)
def touch_record_for_calendar_event(sender, instance, **kwargs):
    touch_record(instance.client_id)


@receiver([post_save, post_delete], sender=LeadPurchase)
def touch_record_for_marketplace_purchase(sender, instance, **kwargs):
    touch_record(instance.crm_record_id)
