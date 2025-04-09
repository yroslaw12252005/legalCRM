from django.shortcuts import render

from leads.models import Record

def client_informs(request, pk):
    get_record_info = Record.objects.get(id=pk)
    return render(request, "client_inform.html", {"info": get_record_info})

