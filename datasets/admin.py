from django.contrib import admin

from .models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "version", "active", "owner", "created_at")
    list_filter = ("created_at", "owner", "domain", "active")
    search_fields = ("name", "description", "owner__username", "domain")
    readonly_fields = ("id", "created_at", "updated_at")
