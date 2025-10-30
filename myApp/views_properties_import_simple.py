"""
SIMPLE CSV Import - No Bullshit Version
Upload CSV → Create Properties → Done
No Redis, Celery, n8n, or any other unnecessary complexity
"""
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
import pandas as pd
import io
import logging

from .models import Property, Company

logger = logging.getLogger(__name__)


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
def import_csv_simple(request: HttpRequest) -> HttpResponse:
    """
    SIMPLE CSV Import
    1. Parse CSV file
    2. Create Property objects directly
    3. Return success/error
    """
    try:
        company = get_company(request)
        uploaded_file = request.FILES.get('csv_file')
        
        if not uploaded_file:
            return JsonResponse({'error': 'Please select a CSV file.'}, status=400)
        
        # Validate file type
        file_name = uploaded_file.name.lower()
        is_excel = file_name.endswith(('.xlsx', '.xls'))
        is_csv = file_name.endswith('.csv')
        
        if not (is_csv or is_excel):
            return JsonResponse({'error': 'Invalid file type. Please upload CSV or Excel file.'}, status=400)
        
        # Parse file
        try:
            if is_excel:
                df = pd.read_excel(uploaded_file)
            else:
                # Try UTF-8 first, fallback to latin-1
                try:
                    content = uploaded_file.read().decode('utf-8')
                    uploaded_file.seek(0)
                    df = pd.read_csv(io.StringIO(content))
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    content = uploaded_file.read().decode('latin-1')
                    df = pd.read_csv(io.StringIO(content))
        except Exception as e:
            logger.error(f"File parsing error: {e}")
            return JsonResponse({'error': f'Failed to parse file: {str(e)}'}, status=400)
        
        if df.empty:
            return JsonResponse({'error': 'The file is empty.'}, status=400)
        
        # Limit rows (optional - remove if you don't want limits)
        max_rows = 500
        if len(df) > max_rows:
            df = df.head(max_rows)
        
        # Normalize column names (case-insensitive)
        column_mapping = {
            'title': ['title', 'property title', 'name', 'property name', 'listing name'],
            'description': ['description', 'desc', 'details', 'property description', 'notes'],
            'price_amount': ['price', 'price_amount', 'rent', 'rental', 'cost', 'amount', 'monthly rent'],
            'city': ['city', 'location', 'locality'],
            'area': ['area', 'neighborhood', 'neighbourhood', 'district', 'barangay', 'subdivision'],
            'beds': ['beds', 'bedrooms', 'bed', 'br', 'brs'],
            'baths': ['baths', 'bathrooms', 'bath', 'ba', 'bas'],
            'hero_image': ['image', 'image_url', 'photo', 'photo_url', 'hero_image', 'image url'],
            'address': ['address', 'street', 'street address'],
        }
        
        # Find matching columns
        normalized_columns = {}
        for standard_col, variations in column_mapping.items():
            for col in df.columns:
                if str(col).lower().strip() in variations:
                    normalized_columns[standard_col] = col
                    break
        
        # Create Properties directly
        created_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Extract data
                title = str(row.get(normalized_columns.get('title', ''), '')).strip()
                if not title or title == 'nan':
                    errors.append(f"Row {idx + 2}: Missing title")
                    continue
                
                # Generate unique slug
                base_slug = slugify(title)
                slug = base_slug
                counter = 1
                while Property.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # Parse price
                price_value = row.get(normalized_columns.get('price_amount', '')) if normalized_columns.get('price_amount') else None
                price_amount = None
                if price_value is not None:
                    try:
                        if not pd.isna(price_value):
                            price_str = str(price_value).replace(',', '').replace('$', '').replace('PHP', '').strip()
                            price_amount = int(float(price_str)) if price_str else None
                    except:
                        price_amount = None
                
                # Parse beds
                beds_value = row.get(normalized_columns.get('beds', '')) if normalized_columns.get('beds') else None
                beds = None
                if beds_value is not None:
                    try:
                        beds = int(float(beds_value)) if not pd.isna(beds_value) else None
                    except:
                        beds = None
                
                # Parse baths
                baths_value = row.get(normalized_columns.get('baths', '')) if normalized_columns.get('baths') else None
                baths = None
                if baths_value is not None:
                    try:
                        baths = int(float(baths_value)) if not pd.isna(baths_value) else None
                    except:
                        baths = None
                
                # Extract other fields
                description = str(row.get(normalized_columns.get('description', ''), '')).strip() if normalized_columns.get('description') else ''
                city = str(row.get(normalized_columns.get('city', ''), '')).strip() if normalized_columns.get('city') else ''
                area = str(row.get(normalized_columns.get('area', ''), '')).strip() if normalized_columns.get('area') else ''
                hero_image = str(row.get(normalized_columns.get('hero_image', ''), '')).strip() if normalized_columns.get('hero_image') else ''
                address = str(row.get(normalized_columns.get('address', ''), '')).strip() if normalized_columns.get('address') else ''
                
                # Create Property directly - no PropertyUpload, no JobTask, no bullshit
                Property.objects.create(
                    company=company,
                    slug=slug,
                    title=title,
                    description=description,
                    city=city,
                    area=area,
                    address=address,
                    price_amount=price_amount,
                    beds=beds,
                    baths=baths,
                    hero_image=hero_image if hero_image else '',
                )
                
                created_count += 1
                
            except Exception as e:
                logger.error(f"Error creating property from row {idx + 2}: {e}")
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        # Return HTML response for HTMX
        return render(request, 'properties/_import_simple_result.html', {
            'success': True,
            'created': created_count,
            'total_rows': len(df),
            'errors': errors[:20] if errors else [],  # Limit errors shown
            'message': f'Successfully imported {created_count} out of {len(df)} properties.'
        })
        
    except ValueError as e:
        return render(request, 'properties/_import_simple_result.html', {
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"CSV import error: {e}", exc_info=True)
        return render(request, 'properties/_import_simple_result.html', {
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)

