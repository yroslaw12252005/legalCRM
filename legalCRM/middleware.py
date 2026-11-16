from .text_normalizer import repair_mojibake_text


class DemoSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.contrib.auth import logout
        from django.http import HttpResponseForbidden
        from django.shortcuts import redirect
        from django.utils import timezone

        from company.demo import delete_demo_company
        from company.models import Companys

        user = getattr(request, "user", None)
        company = getattr(user, "companys", None) if getattr(user, "is_authenticated", False) else None
        if company is not None and company.is_demo:
            request.is_demo_company = True
            if company.demo_expires_at and company.demo_expires_at <= timezone.now():
                company_id = company.pk
                logout(request)
                expired = Companys.objects.filter(pk=company_id, is_demo=True).first()
                if expired:
                    delete_demo_company(expired)
                return redirect("demo_landing")
            if request.method != "GET" and request.FILES:
                return HttpResponseForbidden(
                    "Загрузка файлов отключена в демонстрационном режиме"
                )
        else:
            request.is_demo_company = False
        return self.get_response(request)


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
            if company.is_demo:
                return self.get_response(request)
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
