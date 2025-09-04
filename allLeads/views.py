from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.db.models import Q
from leads.models import Record
from todolist.models import ToDoList
from accounts.models import User
from datetime import datetime

@login_required
def all_leads(request):
    """Главная страница с выводом всех заявок в таблице"""
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    now = f"{year}-{month}-{day}"
    
    todolist = ToDoList.objects.all()
    
    # Фильтрация заявок в зависимости от роли пользователя
    if request.user.status == "Директор КЦ" or request.user.status == "Оператор":
        get_records = Record.objects.filter(companys=request.user.companys)
    else:
        get_records = Record.objects.filter(companys=request.user.companys, felial=request.user.felial)
    
    user = User.objects.all()
    
    return render(request, "all_leads.html", {
        "records": get_records, 
        'users': user, 
        'todolist': todolist, 
        "now": now
    })

@login_required
def filter_by_status(request, status):
    """Фильтрация заявок по статусу"""
    records = Record.objects.filter(
        status=status, 
        companys=request.user.companys, 
        felial=request.user.felial
    )
    return render(request, "all_leads.html", {"records": records})

@login_required
def filter_by_upp(request, filter_upp):
    """Фильтрация заявок по прикрепленному юристу"""
    records = Record.objects.filter(
        employees_UPP=filter_upp, 
        companys=request.user.companys, 
        felial=request.user.felial
    )
    return render(request, "all_leads.html", {"records": records})

@login_required
def filter_by_type(request, type):
    """Фильтрация заявок по типу/тематике"""
    records = Record.objects.filter(
        type=type, 
        companys=request.user.companys, 
        felial=request.user.felial
    )
    return render(request, "all_leads.html", {"records": records})

class SearchView(ListView):
    """Поиск по заявкам"""
    model = Record
    template_name = 'search_results.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Record.objects.filter(
                Q(name__icontains=query) |  # Поиск по части имени
                Q(phone__icontains=query) |  # Поиск по телефону
                Q(description__icontains=query)  # Поиск по описанию
            )
        return Record.objects.none()
