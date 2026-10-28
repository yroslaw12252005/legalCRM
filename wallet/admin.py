from django.contrib import admin

from .models import CompanyWallet, WalletTransaction


@admin.register(CompanyWallet)
class CompanyWalletAdmin(admin.ModelAdmin):
    list_display = ("company", "balance", "updated_at")
    search_fields = ("company__title",)
    readonly_fields = ("balance", "created_at", "updated_at")


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "operation_type", "amount", "balance_after", "created_at")
    list_filter = ("operation_type", "created_at")
    search_fields = ("wallet__company__title", "comment")
    readonly_fields = ("wallet", "operation_type", "amount", "balance_after", "comment", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
