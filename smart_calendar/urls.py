
from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.smart_calendar, name='calendar'),
    path('add_event/<str:pk>/', views.add_event, name='add_event'),
    path('delete_come/<str:pk>/', views.delete_come, name='delete_come'),
]