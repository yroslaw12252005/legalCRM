from django.shortcuts import render
from django.contrib import messages

from .models import Companys
from accounts.models import User

def companys(request):
    companys = Companys.objects.all()

    all_companys = {}
    for company in companys:
        users = User.objects.filter(companys=company.id)
        user = len(users)
        all_companys[company.title] = user
    return render(request, "companys.html", {"all_companys": all_companys})