
from django.urls import path, include
from todolist.views import *

urlpatterns = [
    path('', todolist, name='todolist'),
    path('add_task/', add_task, name='add_task'),
    ]