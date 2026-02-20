from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from leads.models import Record


@login_required
def client_informs(request, pk):
    get_record_info = get_object_or_404(Record, id=pk, companys=request.user.companys)
    return render(request, "client_inform.html", {"info": get_record_info})
