from django.urls import path
from . import views



urlpatterns = [
    path("", views.all_leads, name='all_leads'),
    path("filter/<str:status>/", views.filter_by_status, name='filter_by_status'),
    path("filter_upp/<str:filter_upp>/", views.filter_by_upp, name='filter_by_upp'),
    path("type_filter/<str:type>/", views.filter_by_type, name='filter_by_type'),
    path("search/", views.SearchView.as_view(), name='search'),
] 