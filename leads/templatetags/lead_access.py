from django import template

from leads.access import can_transfer_to_representative, get_phone_display


register = template.Library()


@register.simple_tag
def get_record_phone(user, record, booking_come=None):
    return get_phone_display(user, record, booking_come=booking_come)


@register.simple_tag
def can_show_transfer_button(user, record):
    return can_transfer_to_representative(user, record)
