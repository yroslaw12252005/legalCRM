from django.db import transaction
from django.utils import timezone


SUBSCRIPTION_MANAGER_EMAIL = "yrik@gmail.com"
SUPPORT_EMAIL = "info@rossurist.ru"


def is_subscription_manager(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and (getattr(user, "email", "") or "").strip().casefold()
        == SUBSCRIPTION_MANAGER_EMAIL
    )


@transaction.atomic
def set_company_blocked(company, blocked):
    """Set the company state and keep every attached user flag in sync."""
    from accounts.models import User
    from company.models import Companys

    blocked = bool(blocked)
    Companys.objects.filter(pk=company.pk).update(is_subscription_blocked=blocked)
    User.objects.filter(companys_id=company.pk).update(is_account_blocked=blocked)
    company.is_subscription_blocked = blocked


def enforce_company_subscription(company, today=None):
    """Permanently block an expired company until the manager unlocks it."""
    today = today or timezone.now().date()
    expires_at = company.subscription_expires_at
    if expires_at and expires_at < today and not company.is_subscription_blocked:
        set_company_blocked(company, True)
    return company.is_subscription_blocked


def subscription_warning_days(company, today=None):
    if company.is_subscription_blocked or not company.subscription_expires_at:
        return None
    today = today or timezone.now().date()
    days = (company.subscription_expires_at - today).days
    return days if days in (1, 2, 3) else None
