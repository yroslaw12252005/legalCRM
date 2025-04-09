from django.urls import path, include
from client import views
urlpatterns = [

path("lk_cabinet/<int:pk>/", views.client_informs, name='client_inform'),


]

