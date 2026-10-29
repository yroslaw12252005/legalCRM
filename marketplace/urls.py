from django.urls import path

from . import views


urlpatterns = [
    path("distribute/", views.distribution_list, name="marketplace_distribution"),
    path("distribute/confirm/", views.distribution_confirm, name="marketplace_distribution_confirm"),
    path("distribute/excel/", views.import_leads_from_excel, name="marketplace_excel_import"),
    path("distribute/excel/template/", views.download_excel_template, name="marketplace_excel_template"),
]
