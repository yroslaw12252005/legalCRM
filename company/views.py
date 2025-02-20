from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

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


def company(request, pk):
    companys = Companys.objects.get(id=pk)
    felials = Felial.objects.filter(companys=companys.id)

        # Число сотрудников
    users = len(User.objects.filter(companys=companys.id))
    # Число сделок
    leads = len(Record.objects.filter(companys=companys.id))
    # Число закрытх сделок
    try_leads = len(Record.objects.filter(companys=companys.id, status="Акт"))
    # Число сделок в работе
    in_work_leads = leads - try_leads

    # Число сделок с vk
    vk_qs = len(Record.objects.filter(companys=companys.id, where="VK"))
    site_qs = len(Record.objects.filter(companys=companys.id, where="Сайты"))
    call_qs = len(Record.objects.filter(companys=companys.id, where="Звонки"))
    re_qs = len(Record.objects.filter(companys=companys.id, where="РЕ"))

    all_felial = {}
    for felial in felials:
        all_felial[felial.title] = felial.cites
    return render(request, "company.html", {"all_felial":all_felial})


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