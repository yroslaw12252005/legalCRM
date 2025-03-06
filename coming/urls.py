from django.urls import path
from coming.views import AppointmentsView, AddAppointmentView, ComeTrueView, ComeFalseView

urlpatterns = [
    path('', AppointmentsView.as_view(), name='appointments'),
    path('add/', AddAppointmentView.as_view(), name='add_appointments'),
    path('come-true/<int:pk>/', ComeTrueView.as_view(), name='come_true'),
    path('come-false/<int:pk>/', ComeFalseView.as_view(), name='come_false'),
]