from django.urls import path, include
from felial import views

urlpatterns = [
    path("", views.add_felial, name='add_felial'),

]