from django.urls import path

from . import views


urlpatterns = [
    path("distribute/", views.distribution_list, name="marketplace_distribution"),
    path("distribute/confirm/", views.distribution_confirm, name="marketplace_distribution_confirm"),
]
