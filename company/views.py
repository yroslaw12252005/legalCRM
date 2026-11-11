from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.utils.crypto import get_random_string
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from accounts.views import employees
from .models import Companys
from accounts.models import User
from leads.models import Record
from felial.models import Felial

from .forms import RegCompany
from accounts.forms import AddEmployeesForm,  AddSuperEmployeesForm

import io
import base64
import matplotlib.pyplot as plt
from django.http import HttpResponse


COMPANY_MANAGER_EMAIL = "yrik@gmail.com"
COMPANY_STATS_USERNAMES = {"Yrik", "Сергей"}


def _is_company_manager(user):
    return bool(
        user.is_authenticated
        and (user.email or "").strip().casefold() == COMPANY_MANAGER_EMAIL
    )


def _can_view_company_stats(user):
    return bool(
        user.is_authenticated
        and (_is_company_manager(user) or user.username in COMPANY_STATS_USERNAMES)
    )


def _company_rows():
    rows = []
    for company in Companys.objects.all().order_by("title", "id"):
        records = Record.objects.filter(companys=company)
        admins = list(
            User.objects.filter(companys=company, status="Администратор")
            .order_by("-is_active", "id")
        )
        rows.append(
            {
                "company": company,
                "users": User.objects.filter(companys=company, is_active=True).count(),
                "leads": records.count(),
                "try_leads": records.filter(status="Договор").count(),
                "in_work_leads": records.exclude(status="Договор").count(),
                "vk_qs": records.filter(where="VK").count(),
                "site_qs": records.filter(where="Tilda").count(),
                "call_qs": records.filter(where="Звонок").count(),
                "re_qs": records.filter(where="РЕ").count(),
                "admin": admins[0] if admins else None,
                "admin_count": len(admins),
            }
        )
    return rows


@never_cache
@login_required
def companys(request):
    if not _can_view_company_stats(request.user):
        raise PermissionDenied

    reset_credentials = request.session.pop("company_admin_reset", None)
    return render(
        request,
        "companys.html",
        {
            "company_rows": _company_rows(),
            "can_manage_companies": _is_company_manager(request.user),
            "reset_credentials": reset_credentials,
        },
    )


@require_POST
@login_required
def reset_company_admin_password(request, pk):
    if not _is_company_manager(request.user):
        raise PermissionDenied

    company = get_object_or_404(Companys, pk=pk)
    admin = (
        User.objects.filter(
            companys=company,
            status="Администратор",
            is_active=True,
        )
        .order_by("id")
        .first()
    )
    if admin is None:
        messages.error(request, f"У компании «{company.title}» нет активного администратора")
        return redirect("companys")

    temporary_password = get_random_string(
        16,
        allowed_chars="abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789",
    )
    admin.set_password(temporary_password)
    admin.save(update_fields=["password"])
    if admin.pk == request.user.pk:
        update_session_auth_hash(request, admin)
    request.session["company_admin_reset"] = {
        "company": company.title,
        "username": admin.username,
        "email": admin.email,
        "password": temporary_password,
    }
    messages.success(request, f"Пароль администратора компании «{company.title}» изменён")
    return redirect("companys")


@require_POST
@login_required
def delete_company(request, pk):
    if not _is_company_manager(request.user):
        raise PermissionDenied

    company = get_object_or_404(Companys, pk=pk)
    if request.user.companys_id == company.id:
        messages.error(request, "Нельзя удалить компанию, к которой привязана ваша учётная запись")
        return redirect("companys")

    company_title = company.title
    try:
        with transaction.atomic():
            company.delete()
    except ProtectedError:
        messages.error(
            request,
            f"Компания «{company_title}» не удалена: с ней связана защищённая история покупок или платежей",
        )
    else:
        messages.success(request, f"Компания «{company_title}» и связанные рабочие данные удалены")
    return redirect("companys")



from django.views.generic import TemplateView
#import plotly.offline as opy


class CompanyView(TemplateView):
    template_name = "company.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')

        # Получение основной компании
        company = get_object_or_404(Companys, id=pk)

        # Получение связанных данных
        felials = Felial.objects.filter(companys=company)

        # Статистика для основной компании
        company_stats = self._calculate_company_stats(company)

        # Статистика для филиалов
        branch_stats = self._calculate_branch_stats(felials)

        # Генерация графика
        plot_div = self._generate_plot(company)
        plot_operator = self._generate_plot_operator(company)
        plot_urist = self._generate_plot_urist(company)

        # Сборка контекста
        context.update({
            "title": company.title,
            **company_stats,
            "all_felial": branch_stats,
            "graph": plot_div,
            "graph_operator": plot_operator,
            "graph_urist": plot_urist,
        })
        return context

    def _calculate_company_stats(self, company):
        """Вычисление статистики для главной компании."""
        records = Record.objects.filter(companys=company)

        return {
            "id": company,
            "users": User.objects.filter(companys=company, is_active=True).count(),
            "leads": records.count(),
            "try_leads": records.filter(status="Акт").count(),
            "in_work_leads": records.exclude(status="Акт").count(),
            "vk_qs": records.filter(where="VK").count(),
            "site_qs": records.filter(where="Tilda").count(),
            "call_qs": records.filter(where="Звонок").count(),
            "re_qs": records.filter(where="РЕ").count(),
        }

    def _calculate_branch_stats(self, felials):
        """Вычисление статистики для всех филиалов."""
        branch_stats = {}

        for felial in felials:
            records = Record.objects.filter(felial=felial)

            branch_stats[felial.title] = {
                "users_fl": User.objects.filter(felial=felial, is_active=True).count(),
                "leads_fl": records.count(),
                "try_leads_fl": records.filter(status="Акт").count(),
                "in_work_leads_fl": records.exclude(status="Акт").count(),
                "vk_qs_fl": records.filter(where="VK").count(),
                "site_qs_fl": records.filter(where="Tilda").count(),
                "call_qs_fl": records.filter(where="Звонок").count(),
                "re_qs_fl": records.filter(where="РЕ").count(),
            }
        return branch_stats

    def _generate_plot(self, company):
        records = Record.objects.filter(companys=company)
        statuses = ['Акт', 'В работе', 'Новая', 'Брак', 'Недозвон', 'Перезвон', 'Запись в офис', 'Отказ', 'Онлайн', 'Договор']
        status_counts = [records.filter(status=s).count() for s in statuses]
        plt.figure(figsize=(8, 4))
        plt.bar(statuses, status_counts, color='skyblue')
        plt.title('Распределение сделок по статусам')
        plt.ylabel('Количество')
        plt.xticks(rotation=30, ha='right')
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return f'<img src="data:image/png;base64,{image_base64}"/>'

    def _generate_plot_operator(self, company):
        # Пример: распределение сделок по источникам для операторов
        records = Record.objects.filter(companys=company)
        sources = ['VK', 'Tilda', 'Звонок', 'РЕ']
        source_counts = [records.filter(where=s).count() for s in sources]
        plt.figure(figsize=(6, 4))
        plt.pie(source_counts, labels=sources, autopct='%1.1f%%', startangle=140)
        plt.title('Распределение сделок по источникам')
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return f'<img src="data:image/png;base64,{image_base64}"/>'

    def _generate_plot_urist(self, company):
        # Пример: количество сотрудников по статусу
        users = User.objects.filter(companys=company, is_active=True)
        statuses = users.values_list('status', flat=True).distinct()
        counts = [users.filter(status=s).count() for s in statuses]
        plt.figure(figsize=(6, 4))
        plt.bar(statuses, counts, color='orange')
        plt.title('Сотрудники по статусу')
        plt.ylabel('Количество')
        plt.xticks(rotation=30, ha='right')
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return f'<img src="data:image/png;base64,{image_base64}"/>'


def reg_company(request):
    form = RegCompany(request.POST or None)
    if request.method == "POST":

        if form.is_valid():
            company = form.save()
            return redirect("reg_admin_user", id_company=company.id)

    return render(request, "reg_company.html", {"form": form})

def reg_admin_user(request, id_company):
    company = get_object_or_404(Companys, id=id_company)
    if company.is_solo and User.objects.filter(companys=company).exists():
        messages.warning(request, "Для самостоятельной работы уже создана учётная запись")
        return redirect("all_leads")

    form = AddSuperEmployeesForm(request.POST or None)
    if request.method == "POST":
        form = AddSuperEmployeesForm(request.POST)

        if form.is_valid():
            add_user = form.save(commit=False)
            add_user.companys = company
            add_user.status = 'Администратор'
            add_user.percent = 0
            add_user.bet = 0
            add_user.type_zp = User.SALARY_FIXED
            if company.is_solo:
                main_branch, _ = Felial.objects.get_or_create(
                    companys=company,
                    title="Основной",
                    defaults={"cites": ""},
                )
                add_user.felial = main_branch
            add_user.save()
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password1"]

            user = authenticate(email=email, password=password)
            login(request, user)
            messages.success(request, "Пользователь зарегестрирован")
            return redirect("current_applications")
        else:
            messages.error(request, "An error occured during registration")
            
    return render(request, "reg_admin_user.html", {"form": form, "id_company":id_company})
