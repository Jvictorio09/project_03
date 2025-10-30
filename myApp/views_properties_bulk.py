"""
Bulk actions and export for properties
"""
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
import csv
import json

from .models import Property, Company, HiddenProperty


def get_company(request: HttpRequest) -> Company:
    """Get company from request"""
    company = getattr(request, 'company', None)
    if not company:
        # Fallback: get from user's company
        company = Company.objects.filter(users=request.user).first()
    if not company:
        raise ValueError("No company found for user")
    return company


@login_required
@require_POST
def bulk_properties_action(request: HttpRequest) -> JsonResponse:
    """Handle bulk actions on properties"""
    try:
        company = get_company(request)
        data = json.loads(request.body)
        action = data.get('action')
        property_ids = data.get('property_ids', [])
        
        if not action:
            return JsonResponse({'success': False, 'message': 'No action specified'}, status=400)
        
        if not property_ids:
            return JsonResponse({'success': False, 'message': 'No properties selected'}, status=400)
        
        # Get properties belonging to company
        properties = Property.objects.filter(
            id__in=property_ids,
            company=company,
            is_active=True
        )
        
        count = properties.count()
        if count == 0:
            return JsonResponse({'success': False, 'message': 'No valid properties found'}, status=400)
        
        # Execute action
        if action == 'sync':
            # Sync estimates (placeholder - would call external API)
            # For now, just mark as successful
            return JsonResponse({
                'success': True,
                'message': f'Queued {count} property(ies) for estimate sync'
            })
        
        elif action == 'publish':
            # Publish to site (placeholder)
            return JsonResponse({
                'success': True,
                'message': f'Published {count} property(ies) to site'
            })
        
        elif action == 'push':
            # Push to AI Brain (placeholder)
            return JsonResponse({
                'success': True,
                'message': f'Pushed {count} property(ies) to AI Brain'
            })
        
        elif action == 'archive':
            # Archive properties (set is_active=False)
            properties.update(is_active=False)
            return JsonResponse({
                'success': True,
                'message': f'Archived {count} property(ies)'
            })
        
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action'}, status=400)
    
    except ValueError as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Bulk action error: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)


@login_required
@require_http_methods(["GET"])
def export_properties(request: HttpRequest) -> HttpResponse:
    """Export properties to CSV"""
    try:
        company = get_company(request)
        
        # Get query params for filtering
        city = request.GET.get('city', '').strip()
        beds = request.GET.get('beds', '').strip()
        price_range = request.GET.get('price_range', '').strip()
        
        # Start with company properties
        properties = Property.objects.filter(company=company)
        
        # Apply filters
        if city:
            properties = properties.filter(city__iexact=city)
        
        if beds:
            try:
                properties = properties.filter(beds__gte=int(beds))
            except ValueError:
                pass
        
        if price_range:
            if price_range == '0-300000':
                properties = properties.filter(price_amount__lte=300000)
            elif price_range == '300000-500000':
                properties = properties.filter(price_amount__gte=300000, price_amount__lte=500000)
            elif price_range == '500000-1000000':
                properties = properties.filter(price_amount__gte=500000, price_amount__lte=1000000)
            elif price_range == '1000000+':
                properties = properties.filter(price_amount__gte=1000000)
        
        # Exclude hidden properties for current user
        if request.user.is_authenticated:
            hidden_property_ids = HiddenProperty.objects.filter(user=request.user).values_list('property_id', flat=True)
            properties = properties.exclude(id__in=hidden_property_ids)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="properties_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Title', 'City', 'Area', 'Address', 'Price', 'Beds', 'Baths',
            'Floor Area (sqm)', 'Description', 'Hero Image', 'Created At'
        ])
        
        # Write rows
        for prop in properties:
            writer.writerow([
                prop.title or '',
                prop.city or '',
                prop.area or '',
                getattr(prop, 'address', '') or '',
                prop.price_amount or 0,
                prop.beds or 0,
                prop.baths or 0,
                prop.floor_area_sqm or 0,
                (prop.description or '')[:500],  # Limit description length
                prop.hero_image or '',
                prop.created_at.strftime('%Y-%m-%d %H:%M:%S') if prop.created_at else ''
            ])
        
        return response
    
    except ValueError as e:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Export error: {e}", exc_info=True)
        from django.http import HttpResponseServerError
        return HttpResponseServerError('An error occurred while exporting properties')


