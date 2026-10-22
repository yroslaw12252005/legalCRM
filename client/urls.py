from django.urls import path
from client import views
urlpatterns = [

path("lk_cabinet/<int:pk>/", views.client_informs, name='client_inform'),
path("lk/<uuid:token>/", views.client_portal, name="client_portal"),
path(
    "lk/<uuid:token>/documents/<int:doc_id>/download/",
    views.client_document_download,
    name="client_document_download",
),


]

