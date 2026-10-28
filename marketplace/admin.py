from django.contrib import admin

from .models import LeadPurchase, LeadStreamSettings, MarketplaceLead


@admin.register(MarketplaceLead)
class MarketplaceLeadAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "city", "topic", "status", "buyer", "created_at")
    list_filter = ("status", "city", "topic")
    search_fields = ("name", "phone", "note")


@admin.register(LeadStreamSettings)
class LeadStreamSettingsAdmin(admin.ModelAdmin):
    list_display = ("company", "lead_price", "budget", "spent_amount", "is_enabled", "updated_at")
    list_filter = ("is_enabled",)
    search_fields = ("company__title",)


@admin.register(LeadPurchase)
class LeadPurchaseAdmin(admin.ModelAdmin):
    list_display = ("lead", "company", "price_per_lead", "crm_record", "created_at")
    search_fields = ("lead__name", "lead__phone", "company__title")
    readonly_fields = ("lead", "company", "price_per_lead", "wallet_transaction", "crm_record", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
