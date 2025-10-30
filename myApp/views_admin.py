"""
Admin health page for ingestion monitoring
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Max
from datetime import timedelta
from .models import (
    Company, Lead, Property
)


@staff_member_required
def ingestion_health(request):
    """Lightweight HTML page showing ingestion health per company"""
    
    companies = Company.objects.all()
    
    health_data = []
    for company in companies:
        # Basic stats for each company
        health_data.append({
            'company': company,
            'total_leads': Lead.objects.filter(company=company).count(),
            'total_properties': Property.objects.filter(company=company).count(),
            'recent_leads': Lead.objects.filter(company=company).order_by('-created_at')[:5],
            'recent_properties': Property.objects.filter(company=company).order_by('-created_at')[:5],
        })
    
    context = {
        'health_data': health_data,
        'timestamp': timezone.now()
    }
    
    return render(request, 'admin/ingestion_health.html', context)

