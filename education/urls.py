from django.urls import path

from . import views


urlpatterns = [
    path("", views.material_list, name="education_list"),
    path("categories/add/", views.category_create, name="education_category_add"),
    path("add/", views.material_create, name="education_add"),
    path("<int:pk>/edit/", views.material_edit, name="education_edit"),
    path("<int:pk>/delete/", views.material_delete, name="education_delete"),
    path("<int:pk>/", views.material_detail, name="education_detail"),
]
