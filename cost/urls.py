from django.urls import path, include
from cost import views
urlpatterns = [
    path("/<int:pk>/", views.cost, name='cost'),
    path("user_inform/<int:pk>/", views.percent, name='user_inform'),
]