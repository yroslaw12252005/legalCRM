from django.urls import path, include

from accounts import views

urlpatterns = [
    path("blocked/", views.account_blocked, name="account_blocked"),
    path("register/", views.register_employees, name="reg"),
    path("employees/", views.employees, name='employees'),
    path("delete_employee/<int:pk>/", views.delete_employee, name='delete_employee'),
    path("update_employees/<int:pk>/", views.update_employees, name='update_employee'),
    path("profile/", views.update_profile, name="update_profile"),
]
