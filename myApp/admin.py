from django.contrib import admin
from .models import (
    Property, Lead, PropertyUpload, HiddenProperty, EmailAccount
    # JobTask, JobEvent, LeadMessage, LeadPropertyLink, ChannelConnection - These models don't exist in models.py yet
)

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

# These admin classes are commented out because the models don't exist in models.py yet
# They were created in migrations but the model definitions are missing
# @admin.register(JobTask)
# class JobTaskAdmin(admin.ModelAdmin):
#     list_display = ['kind', 'status', 'organization', 'attempts', 'created_at']
#     list_filter = ['status', 'kind', 'organization', 'created_at']
#     search_fields = ['kind', 'organization__name']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['-created_at']

# @admin.register(JobEvent)
# class JobEventAdmin(admin.ModelAdmin):
#     list_display = ['job', 'event', 'timestamp']
#     list_filter = ['event', 'timestamp']
#     readonly_fields = ['id', 'timestamp']
#     ordering = ['-timestamp']

# @admin.register(LeadMessage)
# class LeadMessageAdmin(admin.ModelAdmin):
#     list_display = ['channel', 'organization', 'lead', 'sender_type', 'created_at']
#     list_filter = ['channel', 'sender_type', 'created_at', 'organization']
#     search_fields = ['text', 'external_thread_id', 'external_msg_id']
#     readonly_fields = ['id', 'created_at']
#     ordering = ['-created_at']

# @admin.register(LeadPropertyLink)
# class LeadPropertyLinkAdmin(admin.ModelAdmin):
#     list_display = ['lead', 'property', 'confidence', 'created_at']
#     list_filter = ['organization', 'created_at']
#     search_fields = ['lead__name', 'property__title']
#     readonly_fields = ['id', 'created_at']
#     ordering = ['-confidence', '-created_at']

# @admin.register(ChannelConnection)
# class ChannelConnectionAdmin(admin.ModelAdmin):
#     list_display = ['organization', 'channel', 'status', 'connected_at']
#     list_filter = ['channel', 'status', 'organization']
#     search_fields = ['organization__name']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['organization', 'channel']

@admin.register(HiddenProperty)
class HiddenPropertyAdmin(admin.ModelAdmin):
    list_display = ['user', 'property', 'hidden_at']
    list_filter = ['hidden_at', 'user']
    search_fields = ['user__email', 'property__title']
    readonly_fields = ['id', 'hidden_at']
    ordering = ['-hidden_at']

@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ['email_address', 'display_name', 'company', 'is_primary', 'is_active', 'is_verified', 'created_at']
    list_filter = ['is_active', 'is_primary', 'is_verified', 'provider', 'created_at']
    search_fields = ['email_address', 'display_name', 'company__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_used_at']
    ordering = ['-is_primary', '-created_at']
