from django.urls import path, include
from cost import views
urlpatterns = [
    path("/<int:pk>/", views.cost, name='cost'),
]