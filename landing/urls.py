from django.urls import path, include
from landing import views
urlpatterns = [
    path("", views.index, name="index"),
    path("demo/", views.demo_landing, name="demo_landing"),
    path("demo/start/", views.demo_start, name="demo_start"),
    path("demo/exit/", views.demo_exit, name="demo_exit"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
]
