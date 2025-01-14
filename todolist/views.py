from django.shortcuts import render
from todolist.models import ToDoList

# Create your views here.
from django.shortcuts import redirect, render
from django.contrib import messages
from .forms import AddTaskForm

def todolist(request):
    todolist = ToDoList.objects.all()
    return render(request, "todolist.html", {'todolist':todolist})


def add_task(request):
    form = AddTaskForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            add_task = form.save(commit=False)
            add_task.user = request.user.id  # The logged-in user
            add_task.save()
            messages.success(request, f"Задача {add_task.title} успешно создана")
            return redirect("todolist")
    return render(request, "add_task.html", {"form": form, 'pk':request.user.id})