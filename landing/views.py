from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from company.demo import cleanup_expired_demo_companies, create_demo_company, delete_demo_company
from company.models import Companys

def index(request):
    return render(
        request,
        "index.html",
        {
            "canonical_url": request.build_absolute_uri(reverse("index")),
            "current_year": timezone.now().year,
        },
    )


def demo_landing(request):
    if request.user.is_authenticated and getattr(request.user.companys, "is_demo", False):
        return redirect("current_applications")
    cleanup_expired_demo_companies(limit=10)
    return render(
        request,
        "demo.html",
        {"active_demo_count": Companys.objects.filter(is_demo=True).count()},
    )


def _client_key(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    address = forwarded.split(",", 1)[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "unknown")
    return address.replace(":", "_")


@require_POST
def demo_start(request):
    if request.user.is_authenticated:
        if getattr(request.user.companys, "is_demo", False):
            return redirect("current_applications")
        messages.info(request, "Вы уже вошли в рабочую компанию. Для демо используйте отдельное окно браузера.")
        return redirect("current_applications")

    cleanup_expired_demo_companies(limit=10)
    rate_key = f"public-demo-start:{_client_key(request)}"
    attempts = cache.get(rate_key, 0)
    if attempts >= getattr(settings, "DEMO_STARTS_PER_HOUR", 3):
        return render(request, "demo.html", {"rate_limited": True}, status=429)

    active_limit = getattr(settings, "DEMO_MAX_ACTIVE_SESSIONS", 50)
    if Companys.objects.filter(is_demo=True, demo_expires_at__gt=timezone.now()).count() >= active_limit:
        return render(request, "demo.html", {"capacity_reached": True}, status=503)

    company, admin = create_demo_company()
    cache.set(rate_key, attempts + 1, timeout=60 * 60)
    login(request, admin, backend="accounts.backends.EmailBackend")
    request.session.set_expiry(int((company.demo_expires_at - timezone.now()).total_seconds()))
    return redirect(f"{reverse('current_applications')}?tour=1")


@require_POST
def demo_exit(request):
    if not request.user.is_authenticated or not getattr(request.user.companys, "is_demo", False):
        return redirect("index")
    company = request.user.companys
    logout(request)
    if Companys.objects.filter(pk=company.pk, is_demo=True).exists():
        delete_demo_company(company)
    return redirect("index")


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("sitemap_xml"))
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /log/",
            "Disallow: /demo/start/",
            "Disallow: /demo/exit/",
            "Disallow: /all-leads/",
            "Disallow: /current-applications/",
            f"Sitemap: {sitemap_url}",
        ]
    )
    return HttpResponse(content, content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    canonical_url = request.build_absolute_uri(reverse("index"))
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{canonical_url}</loc>
    <lastmod>{timezone.now().date().isoformat()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>'''
    return HttpResponse(content, content_type="application/xml; charset=utf-8")
