from django.urls import path
from . import views


urlpatterns = [
    path("", views.get_current_applications, name='desktop'),
    path("bulk_in_work/", views.bulk_in_work, name='desktop_bulk_in_work'),
] 
