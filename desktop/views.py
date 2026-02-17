from django.shortcuts import redirect, render
from leads.models import Record
from accounts.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q

from datetime import date

today = date.today()

STATUS_DIRECTOR_KC = "Директор КЦ"
STATUS_OPERATOR = "Оператор"
STATUS_ADMIN = "Администратор"
STATUS_MANAGER = "Менеджер"
STATUS_DIRECTOR_UPP = "Директор ЮПП"
STATUS_LAWYER_PRIMARY = "Юрист пирвичник"
LEAD_STATUS_NEW = "Новая"
LEAD_STATUS_OFFICE = "Запись в офис"
TOPIC_CHOICES = ["Военка", "Семейная", "Арбитраж", "Военная"]


def _get_desktop_records_for_user(user):
    if user.status == STATUS_DIRECTOR_KC or user.status == STATUS_OPERATOR:
        return Record.objects.filter(companys=user.companys, created_at__date=today, status=LEAD_STATUS_NEW)
    elif user.status == STATUS_MANAGER:
        return Record.objects.filter(companys=user.companys, created_at__date=today, status=LEAD_STATUS_OFFICE)
    else:
        return Record.objects.filter(companys=user.companys, created_at__date=today)


def _can_send_to_work(user):
    return user.status in {STATUS_DIRECTOR_KC, STATUS_OPERATOR, STATUS_ADMIN}


def _can_assign_kc(user):
    return user.status in {STATUS_DIRECTOR_KC, STATUS_ADMIN}


def _can_assign_upp(user):
    return user.status in {STATUS_DIRECTOR_UPP, STATUS_ADMIN}


def _parse_desktop_filters(request):
    search_query = request.GET.get("q", "").strip()
    selected_employee = request.GET.get("employee", "").strip()
    selected_topic = request.GET.get("topic", "").strip()

    # Handle malformed query strings like:
    # q=+79912223344employee=topic=
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


def get_current_applications(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("desktop")
            else:
                messages.warning(request, "Не правильный логин или пароль")
                return redirect("desktop")
        else:
            return render(request, "desktop.html")

    search_query, selected_employee, selected_topic = _parse_desktop_filters(request)
    base_records = _get_desktop_records_for_user(request.user)
    has_filters = bool(search_query or selected_employee or selected_topic)
    get_records = Record.objects.filter(companys=request.user.companys) if has_filters else base_records

    if search_query:
        get_records = get_records.filter(
            Q(name__icontains=search_query)
            | Q(phone__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    if selected_employee:
        get_records = get_records.filter(
            Q(employees_KC=selected_employee) | Q(employees_UPP=selected_employee)
        )

    if selected_topic:
        get_records = get_records.filter(type=selected_topic)

    operators = User.objects.filter(
        companys=request.user.companys,
        status=STATUS_OPERATOR,
    ).order_by("username")

    lawyers = User.objects.filter(
        companys=request.user.companys,
        status=STATUS_LAWYER_PRIMARY,
    ).order_by("username")

    filter_employees = User.objects.filter(
        companys=request.user.companys,
        status__in=[STATUS_OPERATOR, STATUS_LAWYER_PRIMARY],
    ).order_by("username")

    context = {
        "records": get_records,
        "users": User.objects.all(),
        "operators": operators,
        "lawyers": lawyers,
        "filter_employees": filter_employees,
        "topics": TOPIC_CHOICES,
        "search_query": search_query,
        "selected_employee": selected_employee,
        "selected_topic": selected_topic,
        "can_bulk_send_to_work": _can_send_to_work(request.user),
        "can_assign_kc": _can_assign_kc(request.user),
        "can_assign_upp": _can_assign_upp(request.user),
    }

    return render(request, "desktop.html", context)


@login_required
@require_POST
def bulk_in_work(request):
    selected_ids = request.POST.getlist("selected_records")
    if not selected_ids:
        messages.warning(request, "No applications selected")
        return redirect("desktop")

    action = request.POST.get("action", "in_work")
    records_for_user = _get_desktop_records_for_user(request.user).filter(id__in=selected_ids)

    if action == "in_work":
        if not _can_send_to_work(request.user):
            messages.warning(request, "Access denied")
            return redirect("desktop")

        updated_count = records_for_user.update(in_work=1)
        if updated_count:
            messages.success(request, f"Moved to work: {updated_count}")
        else:
            messages.warning(request, "No applications were moved")
        return redirect("desktop")

    if action == "assign_operator":
        if not _can_assign_kc(request.user):
            messages.warning(request, "Access denied")
            return redirect("desktop")

        operator_id = request.POST.get("operator_id")
        operator = User.objects.filter(
            id=operator_id,
            companys=request.user.companys,
            status=STATUS_OPERATOR,
        ).first()

        if not operator:
            messages.warning(request, "Operator not selected")
            return redirect("desktop")

        updated_count = records_for_user.update(employees_KC=operator.username)
        messages.success(request, f"Operator assigned: {updated_count}")
        return redirect("desktop")

    if action == "assign_lawyer":
        if not _can_assign_upp(request.user):
            messages.warning(request, "Access denied")
            return redirect("desktop")

        lawyer_id = request.POST.get("lawyer_id")
        lawyer = User.objects.filter(
            id=lawyer_id,
            companys=request.user.companys,
            status=STATUS_LAWYER_PRIMARY,
        ).first()

        if not lawyer:
            messages.warning(request, "Lawyer not selected")
            return redirect("desktop")

        updated_count = records_for_user.update(employees_UPP=lawyer.username)
        messages.success(request, f"Lawyer assigned: {updated_count}")
        return redirect("desktop")

    messages.warning(request, "Unknown action")
    return redirect("desktop")
