from django.urls import path, include
from cost import views
urlpatterns = [
    path("<int:pk>/", views.cost, name='cost'),
    path("delete/<int:pk>/", views.delete_surcharge, name='delete_surcharge'),
    path("user_inform/<int:pk>/", views.calculating_salaries, name='user_inform'),
]
