from django.contrib import admin
from .models import Property, Lead, PropertyUpload

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'city', 'area', 'price_amount', 'beds', 'baths', 'created_at']
    list_filter = ['city', 'beds', 'baths', 'parking', 'commissionable']
    search_fields = ['title', 'city', 'area', 'description']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-created_at']

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'buy_or_rent', 'budget_max', 'created_at']
    list_filter = ['buy_or_rent', 'created_at']
    search_fields = ['name', 'phone', 'email']
    ordering = ['-created_at']

@admin.register(PropertyUpload)
class PropertyUploadAdmin(admin.ModelAdmin):
    list_display = ['title', 'city', 'status', 'created_at']
    list_filter = ['status', 'city', 'created_at']
    search_fields = ['title', 'city', 'area']
    readonly_fields = ['ai_validation_result', 'validation_chat_history', 'consolidated_information', 'created_at', 'updated_at']
    ordering = ['-created_at']
