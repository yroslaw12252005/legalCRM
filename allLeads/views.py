from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.db.models import Q
from leads.models import Record
from todolist.models import ToDoList
from accounts.models import User
from datetime import datetime


def _parse_filters(request):
    search_query = request.GET.get("q", "").strip()
    selected_employee = request.GET.get("employee", "").strip()
    selected_topic = request.GET.get("topic", "").strip()

    if (
        not selected_employee
        and not selected_topic
        and ("employee=" in search_query or "topic=" in search_query)
    ):
        if "employee=" in search_query:
            query_part, tail = search_query.split("employee=", 1)
            search_query = query_part.strip()
            if "topic=" in tail:
                employee_part, topic_part = tail.split("topic=", 1)
                selected_employee = employee_part.strip()
                selected_topic = topic_part.strip()
            else:
                selected_employee = tail.strip()
        elif "topic=" in search_query:
            query_part, topic_part = search_query.split("topic=", 1)
            search_query = query_part.strip()
            selected_topic = topic_part.strip()

    return search_query, selected_employee, selected_topic


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
        base_records = Record.objects.filter(companys=request.user.companys)
    else:
        base_records = Record.objects.filter(companys=request.user.companys, felial=request.user.felial)

    search_query, selected_employee, selected_topic = _parse_filters(request)
    get_records = base_records

    if search_query:
        get_records = get_records.filter(
            Q(name__icontains=search_query)
            | Q(phone__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    if selected_employee:
        get_records = get_records.filter(
            Q(employees_KC=selected_employee) | Q(employees_UPP=selected_employee) | Q(employees_REP=selected_employee)
        )

    if selected_topic:
        get_records = get_records.filter(type=selected_topic)

    user = User.objects.all()
    filter_employees = User.objects.filter(companys=request.user.companys).order_by("username")
    topics = (
        Record.objects.filter(companys=request.user.companys)
        .exclude(type__isnull=True)
        .exclude(type__exact="")
        .values_list("type", flat=True)
        .distinct()
    )

    return render(request, "all_leads.html", {
        "records": get_records,
        "users": user,
        "todolist": todolist,
        "now": now,
        "filter_employees": filter_employees,
        "topics": topics,
        "search_query": search_query,
        "selected_employee": selected_employee,
        "selected_topic": selected_topic,
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
                Q(name__icontains=query)
                | Q(phone__icontains=query)
                | Q(description__icontains=query)
            )
        return Record.objects.none()
