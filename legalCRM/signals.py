from django.db.models.signals import pre_save
from django.dispatch import receiver

from .text_normalizer import normalize_instance_text_fields


@receiver(pre_save)
def normalize_text_before_save(sender, instance, **kwargs):
    normalize_instance_text_fields(instance)
