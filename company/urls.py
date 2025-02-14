from django.urls import path, include
from company import views

urlpatterns = [
    path('', views.companys)
]