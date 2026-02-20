from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from leads.models import Record

STATUS_DIRECTOR_KC = "Директор КЦ"
STATUS_OPERATOR = "Оператор"
STATUS_ADMIN = "Администратор"
STATUS_MANAGER = "Менеджер"
STATUS_DIRECTOR_UPP = "Директор ЮПП"
STATUS_LAWYER_PRIMARY = "Юрист пирвичник"
STATUS_OP = "ОП"
STATUS_DIRECTOR_REP = "Директор представителей"
STATUS_REPRESENTATIVE = "Представитель"
LEAD_STATUS_NEW = "Новая"
LEAD_STATUS_OFFICE = "Запись в офис"
TOPIC_CHOICES = ["Военка", "Семейная", "Арбитраж", "Военная"]


def _get_desktop_records_for_user(user):
    company_id = user.companys_id
    if not company_id:
        return Record.objects.none()

    today = date.today()
    if user.status in {STATUS_DIRECTOR_KC, STATUS_OPERATOR}:
        return Record.objects.filter(companys_id=company_id, created_at__date=today, status=LEAD_STATUS_NEW)
    if user.status == STATUS_MANAGER:
        return Record.objects.filter(companys_id=company_id, created_at__date=today, status=LEAD_STATUS_OFFICE)
    return Record.objects.filter(companys_id=company_id, created_at__date=today)


def _can_send_to_work(user):
    return user.status in {STATUS_DIRECTOR_KC, STATUS_OPERATOR, STATUS_ADMIN}


def _can_assign_kc(user):
    return user.status in {STATUS_DIRECTOR_KC, STATUS_ADMIN}


def _can_assign_upp(user):
    return user.status in {STATUS_DIRECTOR_UPP, STATUS_ADMIN}


def _can_send_to_representative(user):
    return user.status in {STATUS_DIRECTOR_UPP, STATUS_LAWYER_PRIMARY, STATUS_OP, STATUS_ADMIN}


def _can_assign_rep(user):
    return user.status in {STATUS_DIRECTOR_REP, STATUS_ADMIN}


def _parse_desktop_filters(request):
    search_query = request.GET.get("q", "").strip()
    selected_employee = request.GET.get("employee", "").strip()
    selected_topic = request.GET.get("topic", "").strip()
    selected_status = request.GET.get("status", "").strip()

    # Handle malformed query strings like: q=+79912223344employee=topic=
    if (
        not selected_employee
        and not selected_topic
        and not selected_status
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

    return search_query, selected_employee, selected_topic, selected_status


def get_current_applications(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            username = request.POST.get("username", "")
            password = request.POST.get("password", "")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("desktop")
            messages.warning(request, "Неправильный логин или пароль")
            return redirect("desktop")
        return render(request, "desktop.html")

    search_query, selected_employee, selected_topic, selected_status = _parse_desktop_filters(request)
    company_id = request.user.companys_id

    if not company_id:
        messages.warning(request, "Пользователь не привязан к компании")
        return render(
            request,
            "desktop.html",
            {
                "records": Record.objects.none(),
                "users": User.objects.none(),
                "operators": User.objects.none(),
                "lawyers": User.objects.none(),
                "representatives": User.objects.none(),
                "filter_employees": User.objects.none(),
                "topics": TOPIC_CHOICES,
                "statuses": [],
                "search_query": search_query,
                "selected_employee": selected_employee,
                "selected_topic": selected_topic,
                "selected_status": selected_status,
                "can_bulk_send_to_work": _can_send_to_work(request.user),
                "can_assign_kc": _can_assign_kc(request.user),
                "can_assign_upp": _can_assign_upp(request.user),
                "can_send_to_representative": _can_send_to_representative(request.user),
                "can_assign_rep": _can_assign_rep(request.user),
            },
        )

    base_records = _get_desktop_records_for_user(request.user)
    has_filters = bool(search_query or selected_employee or selected_topic or selected_status)
    get_records = Record.objects.filter(companys_id=company_id) if has_filters else base_records

    if search_query:
        get_records = get_records.filter(
            Q(name__icontains=search_query)
            | Q(phone__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    if selected_employee:
        get_records = get_records.filter(
            Q(employees_KC=selected_employee)
            | Q(employees_UPP=selected_employee)
            | Q(employees_REP=selected_employee)
        )

    if selected_topic:
        get_records = get_records.filter(type=selected_topic)

    if selected_status:
        get_records = get_records.filter(status=selected_status)

    operators = User.objects.filter(companys_id=company_id, status=STATUS_OPERATOR).order_by("username")
    lawyers = User.objects.filter(companys_id=company_id, status__in=[STATUS_LAWYER_PRIMARY, STATUS_OP]).order_by("username")
    filter_employees = User.objects.filter(
        companys_id=company_id,
        status__in=[STATUS_OPERATOR, STATUS_LAWYER_PRIMARY, STATUS_OP, STATUS_REPRESENTATIVE],
    ).order_by("username")
    representatives = User.objects.filter(companys_id=company_id, status=STATUS_REPRESENTATIVE).order_by("username")
    statuses = (
        Record.objects.filter(companys_id=company_id)
        .exclude(status__isnull=True)
        .exclude(status__exact="")
        .values_list("status", flat=True)
        .distinct()
    )

    context = {
        "records": get_records,
        "users": User.objects.filter(companys_id=company_id),
        "operators": operators,
        "lawyers": lawyers,
        "representatives": representatives,
        "filter_employees": filter_employees,
        "topics": TOPIC_CHOICES,
        "statuses": statuses,
        "search_query": search_query,
        "selected_employee": selected_employee,
        "selected_topic": selected_topic,
        "selected_status": selected_status,
        "can_bulk_send_to_work": _can_send_to_work(request.user),
        "can_assign_kc": _can_assign_kc(request.user),
        "can_assign_upp": _can_assign_upp(request.user),
        "can_send_to_representative": _can_send_to_representative(request.user),
        "can_assign_rep": _can_assign_rep(request.user),
    }

    return render(request, "desktop.html", context)


@login_required
@require_POST
def bulk_in_work(request):
    selected_ids = request.POST.getlist("selected_records")
    if not selected_ids:
        messages.warning(request, "No applications selected")
        return redirect("desktop")

    company_id = request.user.companys_id
    if not company_id:
        messages.warning(request, "Company not configured")
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
            companys_id=company_id,
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
            companys_id=company_id,
            status__in=[STATUS_LAWYER_PRIMARY, STATUS_OP],
        ).first()

        if not lawyer:
            messages.warning(request, "Lawyer not selected")
            return redirect("desktop")

        updated_count = records_for_user.update(employees_UPP=lawyer.username)
        messages.success(request, f"Lawyer assigned: {updated_count}")
        return redirect("desktop")

    if action == "to_representative":
        if not _can_send_to_representative(request.user):
            messages.warning(request, "Access denied")
            return redirect("desktop")

        updated_count = records_for_user.update(representative=1)
        if updated_count:
            messages.success(request, f"Moved to representatives: {updated_count}")
        else:
            messages.warning(request, "No applications were moved")
        return redirect("desktop")

    if action == "assign_representative":
        if not _can_assign_rep(request.user):
            messages.warning(request, "Access denied")
            return redirect("desktop")

        representative_id = request.POST.get("representative_id")
        representative = User.objects.filter(
            id=representative_id,
            companys_id=company_id,
            status=STATUS_REPRESENTATIVE,
        ).first()

        if not representative:
            messages.warning(request, "Representative not selected")
            return redirect("desktop")

        updated_count = records_for_user.update(employees_REP=representative.username)
        messages.success(request, f"Representative assigned: {updated_count}")
        return redirect("desktop")

    messages.warning(request, "Unknown action")
    return redirect("desktop")
