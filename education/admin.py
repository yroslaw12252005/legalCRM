from django.contrib import admin

from .models import Category, Material


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "companys")
    search_fields = ("name",)
    list_filter = ("companys",)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "companys", "created_at")
    search_fields = ("title", "body")
    list_filter = ("category", "companys")
