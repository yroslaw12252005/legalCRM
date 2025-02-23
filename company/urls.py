from django.urls import path, include
from company import views
from company.views import CompanyView

urlpatterns = [
    path('', views.companys, name='companys'),
    path('company/<int:pk>/', CompanyView.as_view(), name='company'),
    path('reg_company/', views.reg_company, name='reg_company'),
    path('reg_admin_user/<int:id_company>/', views.reg_admin_user, name='reg_admin_user'),

]