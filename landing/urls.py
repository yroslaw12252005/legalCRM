from django.urls import path, include
from landing import views
urlpatterns = [
    path("", views.index, name='index')
]