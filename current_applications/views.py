from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from allLeads.views import _base_records_for_user, _visible_records_for_user, _with_booking_come


@login_required
def current_applications(request):
    today = date.today()
    records = _with_booking_come(
        _visible_records_for_user(_base_records_for_user(request.user), request.user)
    ).filter(created_at__date=today)

    return render(
        request,
        "current_applications/current_applications.html",
        {
            "records": records.order_by("-created_at"),
            "selected_date": today,
        },
    )

