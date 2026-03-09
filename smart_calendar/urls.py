from django.urls import path
from . import views
urlpatterns = [
    path('', views.smart_calendar, name='calendar'),
    path('add_office_booking/<int:pk>/', views.add_office_booking, name='add_office_booking'),
    path('add_call_event/<int:pk>/', views.add_call_event, name='add_call_event'),
    path('representative/', views.representative_calendar, name='representative_calendar'),
    path('representative/add_event/<str:pk>/', views.add_representative_event, name='add_representative_event'),
    path('delete_come/<str:pk>/', views.delete_come, name='delete_come'),
    path('come/true/<int:pk>/', views.come_True, name='come_true'),
    path('come/false/<int:pk>/', views.come_False, name='come_false'),
    #path('come/update/<int:pk>/', views.update_come, name='update_come'),
]
