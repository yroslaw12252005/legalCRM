from django.contrib import admin
from django.urls import path, include
from coming.views import *

urlpatterns = [
    path('', appointments, name='appointments'),
    path('add_appointments/<int:pk>/', add_appointment, name='add_appointments'),
    path("come_True/<int:pk>/", come_True, name='come_True'),
    path("come_False/<int:pk>/", come_False, name='come_False')
]