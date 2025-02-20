from django.urls import path, include
from company import views

urlpatterns = [
    path('', views.companys, name='companys'),
    path("company/<int:pk>/", views.company, name='company'),
    path('reg_company/', views.reg_company, name='reg_company'),
    path('reg_admin_user/<int:id_company>/', views.reg_admin_user, name='reg_admin_user'),

]