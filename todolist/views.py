from django.shortcuts import render
from todolist.models import ToDoList

# Create your views here.
from django.shortcuts import redirect, render
from django.contrib import messages
from .forms import AddTaskForm

def todolist(request):
    todolist = ToDoList.objects.filter(user=request.user.id)
    return render(request, "todolist.html", {'todolist':todolist})


def add_task(request):
    get_form_task = AddTaskForm(request.POST or None)
    if request.method == "POST":
        if get_form_task.is_valid():
            get_form_task = get_form_task.save(commit=False)
            get_form_task.user = request.user.id  # The logged-in user
            get_form_task.save()
            messages.success(request, f"Задача {get_form_task.title} успешно создана")
            return redirect("todolist")
    return render(request, "add_task.html", {"form": get_form_task, 'pk':request.user.id})

def delete_task(request, pk):
    if request.user.is_authenticated:
        del_task = ToDoList.objects.get(id=pk)
        del_task.delete()
        messages.success(request, "Вы спешно удалил задачу")
        return redirect("home")
    else:
        return redirect("home")