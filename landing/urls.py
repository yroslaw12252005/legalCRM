from django.urls import path, include
from landing import views
urlpatterns = [
    path("", views.index, name="index"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
]
