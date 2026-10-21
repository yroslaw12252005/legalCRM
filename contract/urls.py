from django.urls import path

from . import views


urlpatterns = [
    path("add/<int:record_id>/", views.add_contract, name="add_contract"),
    path("<int:pk>/edit/", views.edit_contract, name="edit_contract"),
]

