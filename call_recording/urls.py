from django.urls import path

from . import views


urlpatterns = [
    path("", views.get_calls, name="get_calls"),
    path("<int:pk>/download/", views.download_call, name="download_call"),
]

