from django.shortcuts import render
from django.contrib import messages

from .models import Companys
from accounts.models import User
from leads.models import Record
from cost.models import Cost

def companys(request):
    companys = Companys.objects.all()

    all_companys = {}
    for company in companys:
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


        all_companys[company.title] = {'users':users, 'leads':leads, 'try_leads':try_leads, "in_work_leads":in_work_leads, "vk_qs":vk_qs, "site_qs":site_qs, "call_qs":call_qs, "re_qs":re_qs}
    return render(request, "companys.html", {"all_companys": all_companys})