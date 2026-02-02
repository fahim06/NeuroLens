from django.contrib import admin
from .models import InferenceRequest


@admin.register(InferenceRequest)
class InferenceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'requested_by', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('requested_by__username',)
    readonly_fields = ('id', 'created_at', 'completed_at')
