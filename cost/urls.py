from django.urls import path, include
from cost import views
urlpatterns = [
    path("salary/", views.salary_list, name="salary_list"),
    path("salary/export/", views.salary_export, name="salary_export"),
    path("<int:pk>/", views.cost, name='cost'),
    path("delete/<int:pk>/", views.delete_surcharge, name='delete_surcharge'),
    path("paid/<int:pk>/", views.mark_surcharge_paid, name="mark_surcharge_paid"),
    path("user_inform/<int:pk>/", views.calculating_salaries, name='user_inform'),
]
