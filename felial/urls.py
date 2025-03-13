from django.urls import path, include
from felial import views

urlpatterns = [
    path("add_felial/", views.add_felial, name='add_felial'),
    path("felial/<int:id_feleal>/", views.felial_info, name='felial_info'),
    path("felials/", views.felials, name='felials'),
]