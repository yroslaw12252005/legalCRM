from django.shortcuts import redirect, render
from coming.models import Coming
from leads.models import Record
from django.http import HttpResponse
from django.contrib import messages


from .forms import AddComing



def appointments(request):
    comings = Coming.objects.all()
    mas = {}
    for i in comings:
        name = Record.objects.get(pk=i.lead_id)
        mas[i.lead_id] = name.name
    print(mas)
    #print(Record.objects.get(pk=Coming.objects.get(pk=4)))
    return render(request, "appointments.html", {"comings": comings, "mas":mas})

def add_appointment(request):
    form = AddComing(request.POST or None)
    if request.method == "POST":

        if form.is_valid():
            add_appointment = form.save()
            return redirect("home")


    return render(request, "add_appointment.html", {"form": form})

def come_True(request, pk):
    comings = Coming.objects.all()
    come_True = Coming.objects.get(id=pk)
    come_True.come = 1
    come_True.save()
    messages.warning(request, "Клиент отмечен как дошедший")
    return render(request, "appointments.html", {"comings": comings})

def come_False(request, pk):
    comings = Coming.objects.all()
    come_True = Coming.objects.get(id=pk)
    come_True.come = 0
    come_True.save()
    messages.warning(request, "Клиент отмечен как недошедший")
    return render(request, "appointments.html", {"comings": comings})

