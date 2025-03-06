from django.shortcuts import redirect, render
from coming.models import Coming
from leads.models import Record
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, CreateView, View
from django.contrib import messages
from django.urls import reverse_lazy

from .forms import AddComing



class AppointmentsView(ListView):
    model = Coming
    template_name = "appointments.html"
    context_object_name = "comings"

    def get_queryset(self):
        return Coming.objects.select_related('lead').all()

class AddAppointmentView(CreateView):
    form_class = AddComing
    template_name = "add_appointment.html"
    success_url = reverse_lazy('home')

class BaseComeView(View):
    come_value = None
    message = ""

    def post(self, request, pk):
        coming = get_object_or_404(Coming, id=pk)
        coming.come = self.come_value
        coming.save()
        messages.warning(request, self.message)
        return redirect('appointments')

class ComeTrueView(BaseComeView):
    come_value = 1
    message = "Клиент отмечен как дошедший"

class ComeFalseView(BaseComeView):
    come_value = 0
    message = "Клиент отмечен как недошедший"
