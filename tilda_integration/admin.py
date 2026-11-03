from django.contrib import admin

from .models import TildaIntegration


@admin.register(TildaIntegration)
class TildaIntegrationAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "branch", "is_active", "last_request_at", "total_processed")
    list_filter = ("is_active", "company")
    search_fields = ("title", "company__title", "public_id")
    readonly_fields = (
        "public_id",
        "secret_hash",
        "previous_secret_hash",
        "previous_secret_valid_until",
        "created_at",
        "updated_at",
        "last_request_at",
        "total_received",
        "total_processed",
        "total_duplicates",
        "total_rejected",
        "total_auth_failed",
        "rate_window_started_at",
        "rate_window_count",
    )
