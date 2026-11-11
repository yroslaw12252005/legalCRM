from django.urls import path, include
from company import views
from company.views import CompanyView

urlpatterns = [
    path('', views.companys, name='companys'),
    path('company/<int:pk>/', CompanyView.as_view(), name='company'),
    path(
        'company/<int:pk>/reset-admin-password/',
        views.reset_company_admin_password,
        name='reset_company_admin_password',
    ),
    path(
        'company/<int:pk>/delete/',
        views.delete_company,
        name='delete_company',
    ),
    path(
        'company/<int:pk>/subscription/',
        views.update_company_subscription,
        name='update_company_subscription',
    ),
    path('company/<int:pk>/block/', views.block_company, name='block_company'),
    path('company/<int:pk>/unblock/', views.unblock_company, name='unblock_company'),
    path('reg_company/', views.reg_company, name='reg_company'),
    path('reg_admin_user/<int:id_company>/', views.reg_admin_user, name='reg_admin_user'),

]
