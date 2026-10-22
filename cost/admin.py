from django.contrib import admin

from .models import Surcharge


@admin.register(Surcharge)
class SurchargeAdmin(admin.ModelAdmin):
    list_display = ("contract", "cost", "dat", "responsible", "is_paid", "paid_at", "paid_by")
    search_fields = ("contract__number", "contract__record__name", "contract__record__phone")
    list_filter = ("is_paid", "dat")
