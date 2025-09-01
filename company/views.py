from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
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


def companys(request):
    companys = Companys.objects.all()

    all_companys = {}
    for company in companys:
        id_companys = company.id
        #Число сотрудников
        users = len(User.objects.filter(companys=company.id))

        # Число сделок
        leads = len(Record.objects.filter(companys=company.id))

        # Число закрытх сделок
        try_leads = len(Record.objects.filter(companys=company.id, status="Акт"))

        # Число сделок в работе
        in_work_leads = leads-try_leads

        # общаяя касса
        #kass_sum = 0
        #for i in leads_qreset:
        #    kassa = Cost.objects.filter(record=i.id)
        #    kass_sum = kass_sum + kassa.cost

        # Число сделок с vk
        vk_qs = len(Record.objects.filter(companys=company.id, where="VK"))
        site_qs = len(Record.objects.filter(companys=company.id, where="Tilda"))
        call_qs = len(Record.objects.filter(companys=company.id, where="Звонок"))
        re_qs = len(Record.objects.filter(companys=company.id, where="РЕ"))


        all_companys[company.title] = {"id":id_companys, 'users':users, 'leads':leads, 'try_leads':try_leads, "in_work_leads":in_work_leads, "vk_qs":vk_qs, "site_qs":site_qs, "call_qs":call_qs, "re_qs":re_qs}
    return render(request, "companys.html", {"all_companys": all_companys})



from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
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
            "users": User.objects.filter(companys=company).count(),
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
                "users_fl": User.objects.filter(felial=felial).count(),
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
        users = User.objects.filter(companys=company)
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
            add_appointment = form.save()

            return redirect("reg_admin_user", id_company=Companys.objects.get(title=form.cleaned_data["title"]).id)

    return render(request, "reg_company.html", {"form": form})

def reg_admin_user(request, id_company):
    form = AddSuperEmployeesForm(request.POST or None)
    if request.method == "POST":
        form = AddSuperEmployeesForm(request.POST)

        if form.is_valid():
            add_user = form.save(commit=False)
            add_user.companys = Companys.objects.get(id=id_company)
            add_user.status = 'Администратор'
            add_user.percent = 0
            add_user.bet = 0
            add_user.type_zp = "Ставка"
            add_user.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]

            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "Пользователь зарегестрирован")
            return redirect("home")
        else:
            messages.error(request, "An error occured during registration")

    return render(request, "reg_admin_user.html", {"form": form, "id_company":id_company})