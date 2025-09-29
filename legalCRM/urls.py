"""
URL configuration for legalCRM project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('landing.urls')),
    path('desktop/', include('desktop.urls')),
    path('all-leads/', include('allLeads.urls')),
    path('log/', include('accounts.urls')),
    path('home/', include('leads.urls')),
    path('todolist/', include('todolist.urls')),
    path('cost/', include('cost.urls')),
    path('companys/', include('company.urls')),
    path('felial/', include('felial.urls')),
    path('calendar/', include('smart_calendar.urls')),
    path('client/', include('client.urls')),
    path('call-recording/', include('call_recording.urls')),
]
