from django.shortcuts import redirect, render
from leads.models import Record
from accounts.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login

from datetime import date
today = date.today()


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
                messages.warning(request, "Не правельный логин или пароль")
                return redirect("desktop")
        else:
            return render(request, "desktop.html")


    if request.user.status == "Директор КЦ" or request.user.status == "Оператор":
        get_records = Record.objects.filter(companys=request.user.companys, created_at__date=today, status="Новая")
    elif request.user.status == "Менеджер":
        get_records = Record.objects.filter(companys=request.user.companys, created_at__date=today, status="Запись в офис")
    else:
        get_records = Record.objects.filter(companys=request.user.companys, created_at__date=today)
    user  =  User.objects.all()
    

    return render(request, "desktop.html", {"records": get_records, 'users':user})

