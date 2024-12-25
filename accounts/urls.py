from django.urls import path, include

from accounts import views

urlpatterns = [
    path("register/", views.register_employees, name="reg"),
    path("employees/", views.employees, name='employees'),
]
