from django.urls import path, include
from leads import views
urlpatterns = [
    path("", views.home, name='home'),
    path("tilda_lead/", views.get_tilda_lead),
    path("logout/", views.logout_user, name='logout'),
    path("record/<int:pk>/", views.record, name='record'),
    path("record/<status>/", views.filter, name='filter'),
    path("delete_record/<int:pk>/", views.delete_record, name='delete_record'),
    path("delete_doc/<int:pk>/", views.delete_doc, name='delete_doc'),
    path("update_record/<int:pk>/", views.update_record, name='update_record'),
    path("in_work/<int:pk>/", views.in_work, name='in_work'),
    path("add_record/", views.add_record, name='add_record'),
    path("register/", include('accounts.urls'), name='register'),
    path("brak/", views.brak, name='brak'),
    path('results/', views.SearchView.as_view(), name='search'),
    path('get_time/', views.get_time, name='get_time'),
    path("records_filt/<filter_upp>/", views.filter_upp, name='filter_upp'),
    path("type_filter/<type>/", views.filter_type, name='filter_type'),

    path("api/v1/felters/", views.FiltersAPI.as_view()),
]
# path("delete_record/<int:pk>/", views.delete_record, name='delete_record'),
#path("update_record/<int:pk>/", views.update_record, name='update_record'),
#path("add_record/", views.add_record, name='add_record'),