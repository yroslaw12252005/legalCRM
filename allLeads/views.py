from datetime import date, datetime



from django.contrib import messages

from django.contrib.auth import authenticate, login

from django.db.models import Q

from django.shortcuts import redirect, render

from django.views.decorators.http import require_POST

from django.views.generic import ListView



from accounts.models import User

from leads.models import Record

from todolist.models import ToDoList



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





def _base_records_for_user(user):

    if user.status in {STATUS_DIRECTOR_KC, STATUS_OPERATOR, STATUS_ADMIN}:

        return Record.objects.filter(companys=user.companys)

    if user.status == STATUS_DIRECTOR_REP:
        return Record.objects.filter(companys=user.companys, representative=True)

    if user.status == STATUS_REPRESENTATIVE:
        return Record.objects.filter(
            companys=user.companys,
            representative=True,
            employees_REP=user.username,
        )

    return Record.objects.filter(companys=user.companys, felial=user.felial)





def _current_records_for_user(user):

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





def _parse_filters(request):
    search_query = request.GET.get("q", "").strip()
    selected_employee = request.GET.get("employee", "").strip()
    selected_topic = request.GET.get("topic", "").strip()
    selected_status = request.GET.get("status", "").strip()


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




def all_leads(request):

    """Главная страница с выводом всех заявок в таблице"""

    if not request.user.is_authenticated:

        if request.method == "POST":

            username = request.POST.get("username", "")

            password = request.POST.get("password", "")

            user = authenticate(request, username=username, password=password)

            if user is not None:

                login(request, user)

                return redirect("all_leads")

            messages.warning(request, "Неправильный логин или пароль")

            return redirect("all_leads")

        return render(request, "all_leads.html")



    current_time = datetime.now()

    now = f"{current_time.year}-{current_time.month}-{current_time.day}"



    todolist = ToDoList.objects.filter(user=request.user.id)



    search_query, selected_employee, selected_topic, selected_status = _parse_filters(request)

    base_records = _base_records_for_user(request.user)

    get_records = base_records



    if search_query:

        query_filter = (

            Q(name__icontains=search_query)

            | Q(phone__icontains=search_query)

            | Q(description__icontains=search_query)

        )

        if search_query.isdigit():

            query_filter |= Q(id=int(search_query))

        get_records = get_records.filter(query_filter)



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



    company_id = request.user.companys_id

    users = User.objects.filter(companys_id=company_id)

    operators = User.objects.filter(companys_id=company_id, status=STATUS_OPERATOR).order_by("username")

    lawyers = User.objects.filter(companys_id=company_id, status__in=[STATUS_LAWYER_PRIMARY, STATUS_OP]).order_by("username")

    representatives = User.objects.filter(companys_id=company_id, status=STATUS_REPRESENTATIVE).order_by("username")

    filter_employees = User.objects.filter(

        companys_id=company_id,

        status__in=[STATUS_OPERATOR, STATUS_LAWYER_PRIMARY, STATUS_OP, STATUS_REPRESENTATIVE],

    ).order_by("username")

    topics = (

        Record.objects.filter(companys_id=company_id)

        .exclude(type__isnull=True)

        .exclude(type__exact="")

        .values_list("type", flat=True)

        .distinct()

    )

    statuses = (

        Record.objects.filter(companys_id=company_id)

        .exclude(status__isnull=True)

        .exclude(status__exact="")

        .values_list("status", flat=True)

        .distinct()

    )



    return render(

        request,

        "all_leads.html",

        {

            "records": get_records,

            "users": users,

            "todolist": todolist,

            "now": now,

            "operators": operators,

            "lawyers": lawyers,

            "representatives": representatives,

            "filter_employees": filter_employees,

            "topics": topics,

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

        },

    )





def filter_by_status(request, status):

    """Фильтрация заявок по статусу"""

    records = Record.objects.filter(

        status=status,

        companys=request.user.companys,

        felial=request.user.felial

    )

    return render(request, "all_leads.html", {"records": records})





def filter_by_upp(request, filter_upp):

    """Фильтрация заявок по прикрепленному юристу"""

    records = Record.objects.filter(

        employees_UPP=filter_upp,

        companys=request.user.companys,

        felial=request.user.felial

    )

    return render(request, "all_leads.html", {"records": records})





def filter_by_type(request, type):

    """Фильтрация заявок по типу/тематике"""

    records = Record.objects.filter(

        type=type,

        companys=request.user.companys,

        felial=request.user.felial

    )

    return render(request, "all_leads.html", {"records": records})





def brak(request):

    records = Record.objects.filter(status="Брак", companys=request.user.companys)

    return render(request, "all_leads.html", {"records": records})





class SearchView(ListView):

    """Поиск по заявкам"""

    model = Record

    template_name = "search_results.html"



    def get_queryset(self):

        query = (self.request.GET.get("q") or "").strip()

        if not query or not self.request.user.is_authenticated:

            return Record.objects.none()

        query_filter = (

            Q(name__icontains=query)

            | Q(phone__icontains=query)

            | Q(description__icontains=query)

        )

        if query.isdigit():

            query_filter |= Q(id=int(query))

        return Record.objects.filter(companys=self.request.user.companys).filter(query_filter)





@require_POST

def bulk_in_work(request):

    if not request.user.is_authenticated:

        return redirect("all_leads")



    selected_ids = request.POST.getlist("selected_records")

    if not selected_ids:

        messages.warning(request, "Нет выбранных заявок")

        return redirect("all_leads")



    company_id = request.user.companys_id

    if not company_id:

        messages.warning(request, "Пользователь не привязан к компании")

        return redirect("all_leads")



    action = request.POST.get("action", "in_work")

    records_for_user = _base_records_for_user(request.user).filter(id__in=selected_ids)



    if action == "in_work":

        if not _can_send_to_work(request.user):

            messages.warning(request, "Недостаточно прав")

            return redirect("all_leads")



        updated_count = records_for_user.update(in_work=1)

        if updated_count:

            messages.success(request, f"Переведено в работу: {updated_count}")

        else:

            messages.warning(request, "Нет заявок для перевода")

        return redirect("all_leads")



    if action == "assign_operator":

        if not _can_assign_kc(request.user):

            messages.warning(request, "Недостаточно прав")

            return redirect("all_leads")



        operator_id = request.POST.get("operator_id")

        operator = User.objects.filter(

            id=operator_id,

            companys_id=company_id,

            status=STATUS_OPERATOR,

        ).first()



        if not operator:

            messages.warning(request, "Оператор не выбран")

            return redirect("all_leads")



        updated_count = records_for_user.update(employees_KC=operator.username)

        messages.success(request, f"Оператор прикреплен: {updated_count}")

        return redirect("all_leads")



    if action == "assign_lawyer":

        if not _can_assign_upp(request.user):

            messages.warning(request, "Недостаточно прав")

            return redirect("all_leads")



        lawyer_id = request.POST.get("lawyer_id")

        lawyer = User.objects.filter(

            id=lawyer_id,

            companys_id=company_id,

            status__in=[STATUS_LAWYER_PRIMARY, STATUS_OP],

        ).first()



        if not lawyer:

            messages.warning(request, "Юрист не выбран")

            return redirect("all_leads")



        updated_count = records_for_user.update(employees_UPP=lawyer.username)

        messages.success(request, f"Юрист прикреплен: {updated_count}")

        return redirect("all_leads")



    if action == "to_representative":

        if not _can_send_to_representative(request.user):

            messages.warning(request, "Недостаточно прав")

            return redirect("all_leads")



        updated_count = records_for_user.update(representative=1)

        if updated_count:

            messages.success(request, f"Передано представителям: {updated_count}")

        else:

            messages.warning(request, "Нет заявок для передачи")

        return redirect("all_leads")



    if action == "assign_representative":

        if not _can_assign_rep(request.user):

            messages.warning(request, "Недостаточно прав")

            return redirect("all_leads")



        representative_id = request.POST.get("representative_id")

        representative = User.objects.filter(

            id=representative_id,

            companys_id=company_id,

            status=STATUS_REPRESENTATIVE,

        ).first()



        if not representative:

            messages.warning(request, "Представитель не выбран")

            return redirect("all_leads")



        updated_count = records_for_user.update(employees_REP=representative.username)

        messages.success(request, f"Представитель прикреплен: {updated_count}")

        return redirect("all_leads")



    messages.warning(request, "Неизвестное действие")

    return redirect("all_leads")

