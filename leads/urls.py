from django.urls import path, include
from leads import views
urlpatterns = [
    path("", views.home, name='home'),
    path("tilda_lead/", views.get_tilda_lead),
    path("logout/", views.logout_user, name='logout'),
    path("record/<int:pk>/", views.record, name='record'),
    path("record/<status>/", views.filter, name='filter'),
    path("delete_record/<int:pk>/", views.delete_record, name='delete_record'),
    path("update_record/<int:pk>/", views.update_record, name='update_record'),
    path("in_work/<int:pk>/", views.in_work, name='in_work'),
    path("add_record/", views.add_record, name='add_record'),
    path("register/", include('accounts.urls'), name='register'),
    path("search_results/", views.search_results, name='search_results'),
    path("brak/", views.brak, name='brak'),
    path('results/', ecomm_views.SearchView.as_view(), name='search'),
]
#path("delete_record/<int:pk>/", views.delete_record, name='delete_record'),
#path("update_record/<int:pk>/", views.update_record, name='update_record'),
#path("add_record/", views.add_record, name='add_record'),