
from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.smart_calendar, name='calendar'),
    path('add_event/', views.add_event, name='add_event'),
]