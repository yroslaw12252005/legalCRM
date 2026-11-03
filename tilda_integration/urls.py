from django.urls import path

from . import views


urlpatterns = [
    path("integrations/tilda/", views.integration_list, name="tilda_integration_list"),
    path("integrations/tilda/create/", views.integration_create, name="tilda_integration_create"),
    path("integrations/tilda/<int:pk>/edit/", views.integration_edit, name="tilda_integration_edit"),
    path("integrations/tilda/<int:pk>/rotate-key/", views.integration_rotate_secret, name="tilda_integration_rotate_secret"),
    path("integrations/tilda/<int:pk>/toggle/", views.integration_toggle, name="tilda_integration_toggle"),
    path("api/v1/webhooks/tilda/<uuid:public_id>/", views.tilda_webhook, name="tilda_webhook"),
]
