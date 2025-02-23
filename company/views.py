from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView

from .models import Companys
from accounts.models import User
from leads.models import Record
from cost.models import Cost
from felial.models import Felial

from .forms import RegCompany
from accounts.forms import AddEmployeesForm

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
        site_qs = len(Record.objects.filter(companys=company.id, where="Сайты"))
        call_qs = len(Record.objects.filter(companys=company.id, where="Звонки"))
        re_qs = len(Record.objects.filter(companys=company.id, where="РЕ"))


        all_companys[company.title] = {"id":id_companys, 'users':users, 'leads':leads, 'try_leads':try_leads, "in_work_leads":in_work_leads, "vk_qs":vk_qs, "site_qs":site_qs, "call_qs":call_qs, "re_qs":re_qs}
    return render(request, "companys.html", {"all_companys": all_companys})


#def company(request, pk):
#    companys = Companys.objects.get(id=pk)
#    felials = Felial.objects.filter(companys=companys.id)
#
#        # Число сотрудников
#    users = len(User.objects.filter(companys=companys.id))
#    # Число сделок
#    leads = len(Record.objects.filter(companys=companys.id))
#    # Число закрытх сделок
#    try_leads = len(Record.objects.filter(companys=companys.id, status="Акт"))
#    # Число сделок в работе
#    in_work_leads = leads - try_leads
#
#    # Число сделок с vk
#    vk_qs = len(Record.objects.filter(companys=companys.id, where="VK"))
#    site_qs = len(Record.objects.filter(companys=companys.id, where="Сайты"))
#    call_qs = len(Record.objects.filter(companys=companys.id, where="Звонки"))
#    re_qs = len(Record.objects.filter(companys=companys.id, where="РЕ"))
#
#    all_felial = {}
#    for felial in felials:
#        # Число сотрудников
#        users_fl = len(User.objects.filter(felial=felial.id))
#
#        # Число сделок
#        leads_fl = len(Record.objects.filter(felial=felial.id))
#
#        # Число закрытх сделок
#        try_leads_fl = len(Record.objects.filter(felial=felial.id, status="Акт"))
#
#        # Число сделок в работе
#        in_work_leads_fl = leads_fl - try_leads_fl
#
#        ## общаяя касса
#        ## kass_sum = 0
#        ## for i in leads_qreset:
#        ##    kassa = Cost.objects.filter(record=i.id)
#        ##    kass_sum = kass_sum + kassa.cost
#
#        # Число сделок с vk
#        vk_qs_fl = len(Record.objects.filter(felial=felial.id, where="VK"))
#        site_qs_fl = len(Record.objects.filter(felial=felial.id, where="Сайты"))
#        call_qs_fl = len(Record.objects.filter(felial=felial.id, where="Звонки"))
#        re_qs_fl = len(Record.objects.filter(felial=felial.id, where="РЕ"))
#
#        all_felial[felial.title] = {'users_fl':users_fl, 'leads_fl':leads_fl, 'try_leads_fl':try_leads_fl, "in_work_leads_fl":in_work_leads_fl, "vk_qs_fl":vk_qs_fl, "site_qs_fl":site_qs_fl, "call_qs_fl":call_qs_fl, "re_qs_fl":re_qs_fl}
#    return render(request, "company.html", {"title":companys.title,'users':users, 'leads':leads, 'try_leads':try_leads, "in_work_leads":in_work_leads, "vk_qs":vk_qs, "site_qs":site_qs, "call_qs":call_qs, "re_qs":re_qs, "all_felial":all_felial})
#
#import plotly.offline as opy
#import plotly.graph_objs as go
#
#class GraphView(TemplateView):
#    template_name = 'graph.html'
#
#    def get_context_data(self, **kwargs):
#
#
#        x = [0,1,2,3,4,5]
#        y = [10,20,30,40,50]
#        trace1 = go.Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104, 'size': 10},
#                            mode="lines",  name='1st Trace')
#
#        data=go.Data([trace1])
#        layout=go.Layout(title="Meine Daten", xaxis={'title':'x1'}, yaxis={'title':'x2'})
#        figure=go.Figure(data=data,layout=layout)
#        div = opy.plot(figure, auto_open=False, output_type='div')
#
#        context['graph'] = div
#
#        return context


from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
import plotly.offline as opy
import plotly.express as px


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

        # Сборка контекста
        context.update({
            "title": company.title,
            **company_stats,
            "all_felial": branch_stats,
            "graph": plot_div
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
            "site_qs": records.filter(where="Сайты").count(),
            "call_qs": records.filter(where="Звонки").count(),
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
                "site_qs_fl": records.filter(where="Сайты").count(),
                "call_qs_fl": records.filter(where="Звонки").count(),
                "re_qs_fl": records.filter(where="РЕ").count(),
            }
        return branch_stats

    def _generate_plot(self, company):
        """Генерация графика Plotly."""

        import numpy as np
        import plotly
        import plotly.graph_objects as go
        import plotly.offline as pyo
        feleals = []
        records = []
        # countries on x-axis
        #for i in Felial.objects.filter(companys=company):
        #    feleals = [i.title]
        #    for l in Record.objects.filter(felial=i.id):
        #        records = [l]

        for i in Felial.objects.filter(companys=company):
            feleals.append(i.title)
            records.append(Record.objects.filter(felial=i.id).count())
        layout=go.Layout(title="Число заявок на филиал", xaxis={'title':'Фелиалы'}, yaxis={'title':'Заявки'})
        fig = go.Figure([go.Bar(y=records,x=feleals
                                )],layout=layout)
        return opy.plot(fig, auto_open=False, output_type='div')
def reg_company(request):
    form = RegCompany(request.POST or None)
    if request.method == "POST":

        if form.is_valid():
            add_appointment = form.save()

            return redirect("reg_admin_user", id_company=Companys.objects.get(title=form.cleaned_data["title"]).id)

    return render(request, "reg_company.html", {"form": form})

def reg_admin_user(request, id_company):
    form = AddEmployeesForm(request.POST or None)
    if request.method == "POST":
        form = AddEmployeesForm(request.POST)

        if form.is_valid():
            add_user = form.save(commit=False)
            add_user.companys = Companys.objects.get(id=id_company)  # The logged-in user
            add_user.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            status = form.cleaned_data["status"]
            email = form.cleaned_data["email"]

            user = authenticate(username=username, email=email, status=status, password=password)
            login(request, user)
            messages.success(request, "Пользователь зарегестрирован")
            return redirect("home")
        else:
            messages.error(request, "An error occured during registration")

    return render(request, "reg_admin_user.html", {"form": form, "id_company":id_company})