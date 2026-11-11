from .text_normalizer import repair_mojibake_text


class CompanySubscriptionMiddleware:
    ALLOWED_URL_NAMES = {"account_blocked", "logout"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.shortcuts import redirect
        from django.urls import Resolver404, resolve

        from accounts.models import User
        from company.subscriptions import (
            enforce_company_subscription,
            is_subscription_manager,
        )

        user = getattr(request, "user", None)
        company = getattr(user, "companys", None) if getattr(user, "is_authenticated", False) else None
        if company is not None:
            enforce_company_subscription(company)

            if user.is_account_blocked != company.is_subscription_blocked:
                User.objects.filter(pk=user.pk).update(
                    is_account_blocked=company.is_subscription_blocked
                )
                user.is_account_blocked = company.is_subscription_blocked

            if company.is_subscription_blocked and not is_subscription_manager(user):
                try:
                    url_name = resolve(request.path_info).url_name
                except Resolver404:
                    url_name = None
                if url_name not in self.ALLOWED_URL_NAMES:
                    return redirect("account_blocked")

        return self.get_response(request)


class RequestUserTextNormalizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            for field_name in ("status", "username", "first_name", "last_name"):
                current = getattr(user, field_name, None)
                if not isinstance(current, str):
                    continue
                fixed = repair_mojibake_text(current)
                if fixed != current:
                    setattr(user, field_name, fixed)
        return self.get_response(request)
