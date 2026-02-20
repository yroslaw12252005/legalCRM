from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from todolist.models import ToDoList

from .forms import AddTaskForm


@login_required
def todolist(request):
    todo_items = ToDoList.objects.filter(user=request.user.id)
    return render(request, "todolist.html", {"todolist": todo_items})


@login_required
def add_task(request):
    get_form_task = AddTaskForm(request.POST or None)
    if request.method == "POST" and get_form_task.is_valid():
        get_form_task = get_form_task.save(commit=False)
        get_form_task.user = request.user.id
        get_form_task.save()
        messages.success(request, f"Задача {get_form_task.title} успешно создана")
        return redirect("todolist")
    return render(request, "add_task.html", {"form": get_form_task, "pk": request.user.id})


@login_required
def delete_task(request, pk):
    del_task = get_object_or_404(ToDoList, id=pk, user=request.user.id)
    del_task.delete()
    messages.success(request, "Вы успешно удалили задачу")
    return redirect("home")
