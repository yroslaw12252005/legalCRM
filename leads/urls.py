from django.urls import path, include
from leads import views
urlpatterns = [
    path("tilda_lead/", views.get_tilda_lead),
    path("logout/", views.logout_user, name='logout'),
    path("record/<int:pk>/", views.record, name='record'),
    path("delete_record/<int:pk>/", views.delete_record, name='delete_record'),
    path("delete_doc/<int:pk>/", views.delete_doc, name='delete_doc'),
    path("update_record/<int:pk>/", views.update_record, name='update_record'),
    path("in_work/<int:pk>/", views.in_work, name='in_work'),
    path("paid_online/<int:pk>/", views.paid_online, name='paid_online'),
    path("to_representative/<int:pk>/", views.to_representative, name='to_representative'),
    path("download_document/<int:doc_id>/", views.download_document, name='download_document'),
    path("add_record/", views.add_record, name='add_record'),
    path("register/", include('accounts.urls'), name='register'),
    path('get_time/', views.get_time, name='get_time'),
]
# path("delete_record/<int:pk>/", views.delete_record, name='delete_record'),
#path("update_record/<int:pk>/", views.update_record, name='update_record'),
#path("add_record/", views.add_record, name='add_record'),
