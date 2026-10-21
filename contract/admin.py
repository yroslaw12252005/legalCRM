from django.contrib import admin

from .models import Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("number", "record", "amount", "initial_payment", "contract_date")
    search_fields = ("number", "record__name", "record__phone")
    list_filter = ("contract_date",)

