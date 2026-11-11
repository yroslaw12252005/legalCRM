from .subscriptions import SUPPORT_EMAIL, subscription_warning_days


def subscription_status(request):
    user = getattr(request, "user", None)
    company = getattr(user, "companys", None) if getattr(user, "is_authenticated", False) else None
    if company is None:
        return {}
    return {
        "subscription_warning_days": subscription_warning_days(company),
        "subscription_expires_at": company.subscription_expires_at,
        "subscription_support_email": SUPPORT_EMAIL,
    }
