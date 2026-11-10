from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

def index(request):
    return render(
        request,
        "index.html",
        {
            "canonical_url": request.build_absolute_uri(reverse("index")),
            "current_year": timezone.now().year,
        },
    )


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("sitemap_xml"))
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /log/",
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
