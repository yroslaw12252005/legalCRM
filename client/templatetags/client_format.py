from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def money(value):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return "0"

    decimals = 0 if amount == amount.to_integral() else 2
    return f"{amount:,.{decimals}f}".replace(",", " ").replace(".", ",")
