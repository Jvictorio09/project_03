"""
Property Import Views - HTMX Endpoints Only
All endpoints return HTML fragments for modal body swapping
"""
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.text import slugify
from django.core.cache import cache
from django.conf import settings
import json
import re
import uuid
import logging

from .models import Property, PropertyUpload, Company
from .forms import PropertyUploadForm, PropertyForm
from .utils.cloudinary_utils import upload_to_cloudinary

logger = logging.getLogger(__name__)

# Rate limiting: max 5 uploads per minute per org/IP
MAX_UPLOADS_PER_MINUTE = 5

def get_company(request: HttpRequest) -> Company:
    """Get company from request (set by middleware)"""
    company = getattr(request, 'company', None)
    if not company:
        # Fallback: get from user's company
        company = Company.objects.filter(users=request.user).first()
    if not company:
        raise ValueError("No company found for user")
    return company


def check_rate_limit(request: HttpRequest, company: Company) -> tuple[bool, str]:
    """Check if user has exceeded rate limit"""
    cache_key = f"import_rate_limit:{company.id}:{request.META.get('REMOTE_ADDR', 'unknown')}"
    count = cache.get(cache_key, 0)
    
    if count >= MAX_UPLOADS_PER_MINUTE:
        return False, f"Rate limit exceeded. Maximum {MAX_UPLOADS_PER_MINUTE} imports per minute. Please wait and try again."
    
    cache.set(cache_key, count + 1, 60)  # 60 second window
    return True, ""


@login_required
@require_http_methods(["GET"])
def add_property_modal(request: HttpRequest) -> HttpResponse:
    """Return the tabbed import UI fragment"""
    try:
        company = get_company(request)
        return render(request, 'properties/_import_modal.html', {
            'organization': organization
        })
    except Exception as e:
        logger.error(f"Error loading import modal: {e}", extra={
            'user_id': request.user.id,
            'exception': str(e)
        })
        return render(request, 'properties/_error_fragment.html', {
            'error': 'Unable to load import form. Please refresh and try again.',
            'error_detail': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def edit_property_modal(request: HttpRequest, property_id) -> HttpResponse:
    """Modal content for editing an existing property"""
    try:
        try:
            company = get_company(request)
        except ValueError as e:
            logger.error(f"Organization error in edit_property_modal: {e}", extra={
                'user_id': request.user.id if hasattr(request, 'user') else None
            })
            return render(request, 'properties/_error_fragment.html', {
                'error': 'Unable to determine your company. Please refresh the page.'
            }, status=400)
        
        # Get property (Django URL converter handles UUID conversion)
        try:
            property_obj = Property.objects.get(id=property_id, company=company)
        except Property.DoesNotExist:
            logger.warning(f"Property not found: {property_id}", extra={
                'user_id': request.user.id if hasattr(request, 'user') else None,
                'property_id': str(property_id),
                'company_id': str(company.id) if company else None
            })
            return render(request, 'properties/_error_fragment.html', {
                'error': 'Property not found or you do not have access to it'
            }, status=404)
        except Exception as e:
            logger.error(f"Error fetching property: {e}", exc_info=True, extra={
                'user_id': request.user.id if hasattr(request, 'user') else None,
                'property_id': str(property_id)
            })
            return render(request, 'properties/_error_fragment.html', {
                'error': 'An error occurred while loading the property'
            }, status=500)
        
        if request.method == 'POST':
            # Store original title before form processing
            original_title = property_obj.title
            form = PropertyForm(request.POST, request.FILES, instance=property_obj)
            if form.is_valid():
                property_obj = form.save(commit=False)
                # Only update slug if title changed
                if property_obj.title and property_obj.title != original_title:
                    # Generate new slug from title
                    new_slug = slugify(property_obj.title)
                    # Ensure slug is unique - append property ID if needed
                    if Property.objects.filter(slug=new_slug).exclude(id=property_obj.id).exists():
                        new_slug = f"{new_slug}-{str(property_obj.id)[:8]}"
                    property_obj.slug = new_slug
                property_obj.save()
                
                # Return success response for HTMX
                return render(request, 'partials/property_success.html', {
                    'property': property_obj,
                    'message': 'Property updated successfully!'
                })
            else:
                # Return form with errors
                return render(request, 'partials/edit_property_form.html', {
                    'form': form,
                    'property': property_obj
                })
        else:
            try:
                form = PropertyForm(instance=property_obj)
                return render(request, 'partials/edit_property_form.html', {
                    'form': form,
                    'property': property_obj
                })
            except Exception as e:
                logger.error(f"Error initializing PropertyForm: {e}", exc_info=True, extra={
                    'user_id': request.user.id if hasattr(request, 'user') else None,
                    'property_id': str(property_id)
                })
                return render(request, 'properties/_error_fragment.html', {
                    'error': 'An error occurred while loading the edit form',
                    'error_detail': str(e)
                }, status=500)
    except ValueError as e:
        return render(request, 'properties/_error_fragment.html', {
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Error in edit_property_modal: {e}", exc_info=True, extra={
            'user_id': request.user.id,
            'property_id': property_id
        })
        return render(request, 'properties/_error_fragment.html', {
            'error': 'An error occurred while loading the edit form. Please try again.',
            'error_detail': str(e)
        }, status=500)


@login_required
@require_POST
def import_manual(request: HttpRequest) -> HttpResponse:
    """Handle manual form submission"""
    try:
        company = get_company(request)
        
        # Rate limit check
        allowed, error_msg = check_rate_limit(request, company)
        if not allowed:
            return render(request, 'properties/_error_fragment.html', {
                'error': error_msg
            }, status=429)
        
        form = PropertyUploadForm(request.POST, request.FILES)
        
        if not form.is_valid():
            # Return form with errors
            return render(request, 'properties/_import_manual_form.html', {
                'form': form,
                'errors': form.errors
            }, status=400)
        
        # Create PropertyUpload
        upload = form.save(commit=False)
        if not upload.company:
            upload.company = company
        upload.status = 'uploading'
        upload.save()
        
        # Handle image upload
        hero_image = request.FILES.get('hero_image')
        if hero_image:
            # Validate file size (10MB max)
            if hero_image.size > 10 * 1024 * 1024:
                upload.delete()
                return render(request, 'properties/_error_fragment.html', {
                    'error': 'Image file is too large. Maximum size is 10MB. Please compress and try again.'
                }, status=400)
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if hero_image.content_type not in allowed_types:
                upload.delete()
                return render(request, 'properties/_error_fragment.html', {
                    'error': 'Invalid image type. Please upload JPEG, PNG, or WebP images only.'
                }, status=400)
            
            try:
                cloudinary_result = upload_to_cloudinary(hero_image, folder="property_uploads")
                upload.hero_image = cloudinary_result['secure_url']
            except Exception as e:
                logger.error(f"Cloudinary upload failed: {e}", extra={
                    'upload_id': upload.id,
                    'user_id': request.user.id
                })
                upload.delete()
                return render(request, 'properties/_error_fragment.html', {
                    'error': 'Failed to upload image. Please check your connection and try again.',
                    'error_detail': str(e)
                }, status=500)
        
        # Transition to processing
        upload.status = 'processing'
        upload.save()
        
        # Kick off light AI validation
        start_light_validation(upload)
        
        # Return status fragment
        return render(request, 'properties/_import_status.html', {
            'upload': upload
        })
        
    except ValueError as e:
        return render(request, 'properties/_error_fragment.html', {
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Manual import error: {e}", extra={
            'user_id': request.user.id,
            'exception': str(e)
        })
        return render(request, 'properties/_error_fragment.html', {
            'error': 'An error occurred while processing your property. Please try again.',
            'error_detail': str(e)
        }, status=500)


@login_required
@require_POST
def import_ai(request: HttpRequest) -> HttpResponse:
    """Handle AI text import"""
    try:
        company = get_company(request)
        
        # Rate limit check
        allowed, error_msg = check_rate_limit(request, company)
        if not allowed:
            return render(request, 'properties/_error_fragment.html', {
                'error': error_msg
            }, status=429)
        
        property_text = request.POST.get('property_text', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        
        if not property_text:
            return render(request, 'properties/_import_ai_form.html', {
                'error': 'Please paste property description text.'
            }, status=400)
        
        # Create PropertyUpload
        upload = PropertyUpload.objects.create(
            company=company,
            status='uploading',
            description=property_text[:5000]  # Limit length
        )
        
        # Extract data using lightweight extraction
        extracted_data = extract_property_data(property_text)
        
        upload.title = extracted_data.get('title') or 'Untitled Property'
        upload.price_amount = extracted_data.get('price_amount')
        upload.city = extracted_data.get('city') or ''
        upload.area = extracted_data.get('area') or ''
        upload.beds = extracted_data.get('beds')
        upload.baths = extracted_data.get('baths')
        
        if image_url:
            upload.hero_image = image_url
        
        # Transition to processing
        upload.status = 'processing'
        upload.save()
        
        # Kick off light AI validation
        start_light_validation(upload)
        
        # Return status fragment
        return render(request, 'properties/_import_status.html', {
            'upload': upload,
            'extracted_preview': extracted_data
        })
        
    except ValueError as e:
        return render(request, 'properties/_error_fragment.html', {
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"AI import error: {e}", extra={
            'user_id': request.user.id,
            'exception': str(e)
        })
        return render(request, 'properties/_error_fragment.html', {
            'error': 'An error occurred while processing your property. Please try again.',
            'error_detail': str(e)
        }, status=500)


@login_required
@require_POST
def import_csv(request: HttpRequest) -> HttpResponse:
    """Handle CSV/Excel file import"""
    try:
        company = get_company(request)
        
        # Rate limit check
        allowed, error_msg = check_rate_limit(request, company)
        if not allowed:
            return render(request, 'properties/_error_fragment.html', {
                'error': error_msg
            }, status=429)
        
        uploaded_file = request.FILES.get('csv_file')
        if not uploaded_file:
            return render(request, 'properties/_import_csv_form.html', {
                'error': 'Please select a CSV or Excel file.'
            }, status=400)
        
        # Validate file type
        file_name = uploaded_file.name.lower()
        is_excel = file_name.endswith(('.xlsx', '.xls'))
        is_csv = file_name.endswith('.csv')
        
        if not (is_csv or is_excel):
            return render(request, 'properties/_import_csv_form.html', {
                'error': 'Invalid file type. Please upload a CSV or Excel file (.csv, .xlsx, .xls).'
            }, status=400)
        
        # Parse file
        import pandas as pd
        import io
        
        try:
            if is_excel:
                df = pd.read_excel(uploaded_file)
            else:
                # Try different encodings for CSV
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
            return render(request, 'properties/_import_csv_form.html', {
                'error': f'Failed to parse file: {str(e)}. Please check the file format.'
            }, status=400)
        
        # Validate CSV has data
        if df.empty:
            return render(request, 'properties/_import_csv_form.html', {
                'error': 'The file is empty. Please upload a file with property data.'
            }, status=400)
        
        # Limit to 100 rows per import
        max_rows = 100
        if len(df) > max_rows:
            df = df.head(max_rows)
            warning_message = f'File contains more than {max_rows} rows. Only the first {max_rows} properties will be imported.'
        else:
            warning_message = None
        
        # Normalize column names (case-insensitive, handle common variations)
        column_mapping = {
            'title': ['title', 'property title', 'name', 'property name', 'listing name'],
            'description': ['description', 'desc', 'details', 'property description', 'notes'],
            'price_amount': ['price', 'price_amount', 'rent', 'rental', 'cost', 'amount', 'monthly rent'],
            'city': ['city', 'location', 'locality'],
            'area': ['area', 'neighborhood', 'neighbourhood', 'district', 'barangay', 'subdivision'],
            'beds': ['beds', 'bedrooms', 'bed', 'br', 'brs'],
            'baths': ['baths', 'bathrooms', 'bath', 'ba', 'bas'],
            'hero_image': ['image', 'image_url', 'photo', 'photo_url', 'hero_image', 'image url'],
        }
        
        normalized_columns = {}
        for standard_col, variations in column_mapping.items():
            for col in df.columns:
                if str(col).lower().strip() in variations:
                    normalized_columns[standard_col] = col
                    break
        
        # Create PropertyUpload records for each row
        uploads = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Extract data from row
                upload_data = {
                    'company': company,
                    'status': 'uploading',
                    'title': str(row.get(normalized_columns.get('title', ''), '')).strip() if normalized_columns.get('title') else None,
                    'description': str(row.get(normalized_columns.get('description', ''), '')).strip() if normalized_columns.get('description') else '',
                    'city': str(row.get(normalized_columns.get('city', ''), '')).strip() if normalized_columns.get('city') else '',
                    'area': str(row.get(normalized_columns.get('area', ''), '')).strip() if normalized_columns.get('area') else '',
                    'hero_image': str(row.get(normalized_columns.get('hero_image', ''), '')).strip() if normalized_columns.get('hero_image') else '',
                }
                
                # Parse price
                price_value = row.get(normalized_columns.get('price_amount', '')) if normalized_columns.get('price_amount') else None
                if price_value is not None:
                    try:
                        if pd.isna(price_value):
                            upload_data['price_amount'] = None
                        else:
                            price_str = str(price_value).replace(',', '').replace('$', '').replace('PHP', '').strip()
                            upload_data['price_amount'] = int(float(price_str)) if price_str else None
                    except:
                        upload_data['price_amount'] = None
                
                # Parse beds
                beds_value = row.get(normalized_columns.get('beds', '')) if normalized_columns.get('beds') else None
                if beds_value is not None:
                    try:
                        upload_data['beds'] = int(float(beds_value)) if not pd.isna(beds_value) else None
                    except:
                        upload_data['beds'] = None
                
                # Parse baths
                baths_value = row.get(normalized_columns.get('baths', '')) if normalized_columns.get('baths') else None
                if baths_value is not None:
                    try:
                        upload_data['baths'] = int(float(baths_value)) if not pd.isna(baths_value) else None
                    except:
                        upload_data['baths'] = None
                
                # Create PropertyUpload
                upload = PropertyUpload.objects.create(**upload_data)
                
                # Transition to processing
                upload.status = 'processing'
                upload.save()
                
                # Start AI enrichment (async via JobTask)
                if company:
                    JobTask.objects.create(
                        company=company,
                        kind='property_ai_enrichment',
                        payload={
                            'upload_id': str(upload.id),
                            'source': 'csv_import',
                            'row_index': int(idx)
                        },
                        status='pending'
                    )
                
                # Also run light enrichment synchronously for immediate feedback
                try:
                    enrich_property_with_ai(upload)
                    # Auto-complete if critical fields are present
                    if upload.title and upload.price_amount and upload.city:
                        upload.status = 'complete'
                        upload.save()
                        # Create Property immediately
                        try:
                            create_property_from_upload(upload)
                        except Exception as e:
                            logger.error(f"Failed to create property from upload {upload.id}: {e}")
                except Exception as e:
                    logger.warning(f"Synchronous AI enrichment failed for upload {upload.id}: {e}")
                    # Still mark as processing for async enrichment
                    start_light_validation(upload)
                
                uploads.append(upload)
                
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                errors.append(f"Row {idx + 2}: {str(e)}")  # +2 because Excel is 1-indexed and has header
        
        # Return batch import status
        return render(request, 'properties/_import_batch_status.html', {
            'total_rows': len(df),
            'successful': len(uploads),
            'failed': len(errors),
            'errors': errors[:10],  # Show first 10 errors
            'uploads': uploads[:5],  # Show first 5 uploads
            'warning': warning_message
        })
        
    except ValueError as e:
        return render(request, 'properties/_error_fragment.html', {
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"CSV import error: {e}", extra={
            'user_id': request.user.id,
            'exception': str(e)
        })
        return render(request, 'properties/_error_fragment.html', {
            'error': 'An error occurred while processing your file. Please check the format and try again.',
            'error_detail': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def import_csv_template(request: HttpRequest) -> HttpResponse:
    """Download CSV template file"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="property_import_template.csv"'
    
    writer = csv.writer(response)
    # Write header row
    writer.writerow([
        'Title',
        'Price',
        'City',
        'Area',
        'Beds',
        'Baths',
        'Description',
        'Image URL'
    ])
    
    # Write example rows
    writer.writerow([
        'Luxury 2BR Condo in BGC',
        '3500',
        'Makati',
        'BGC',
        '2',
        '2',
        'Modern condo with city views, pool, gym',
        'https://example.com/image.jpg'
    ])
    writer.writerow([
        'Spacious 3BR House',
        '5500',
        'Quezon City',
        'Ortigas',
        '3',
        '3',
        'Family-friendly house with garden',
        ''
    ])
    
    return response


@login_required
@require_http_methods(["GET"])
def import_status(request: HttpRequest, upload_id: str) -> HttpResponse:
    """Return status fragment (pollable)"""
    try:
        company = get_company(request)
        upload = get_object_or_404(PropertyUpload, id=upload_id, company=company)
        
        return render(request, 'properties/_import_status.html', {
            'upload': upload
        })
    except Exception as e:
        logger.error(f"Status check error: {e}", extra={
            'upload_id': upload_id,
            'user_id': request.user.id
        })
        return render(request, 'properties/_error_fragment.html', {
            'error': 'Unable to check status. Please refresh.'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def import_validate(request: HttpRequest, upload_id: str) -> HttpResponse:
    """Return validation chat fragment"""
    try:
        company = get_company(request)
        upload = get_object_or_404(PropertyUpload, id=upload_id, company=company)
        
        if upload.status != 'validation':
            return render(request, 'properties/_error_fragment.html', {
                'error': 'This property is not in validation status.'
            }, status=400)
        
        # Get next question
        next_question = get_next_validation_question(upload)
        
        return render(request, 'properties/_import_validation.html', {
            'upload': upload,
            'next_question': next_question,
            'chat_history': upload.validation_chat_history or []
        })
    except Exception as e:
        logger.error(f"Validation GET error: {e}", extra={
            'upload_id': upload_id,
            'user_id': request.user.id
        })
        return render(request, 'properties/_error_fragment.html', {
            'error': 'Unable to load validation chat.'
        }, status=500)


@login_required
@require_POST
def import_validate_submit(request: HttpRequest, upload_id: str) -> HttpResponse:
    """Handle validation chat reply"""
    try:
        company = get_company(request)
        upload = get_object_or_404(PropertyUpload, id=upload_id, company=company)
        
        user_message = request.POST.get('user_message', '').strip()
        
        if not user_message:
            return render(request, 'properties/_import_validation.html', {
                'upload': upload,
                'next_question': get_next_validation_question(upload),
                'chat_history': upload.validation_chat_history or [],
                'error': 'Please provide an answer.'
            }, status=400)
        
        # Append to chat history
        chat_history = upload.validation_chat_history or []
        chat_history.append({
            'role': 'user',
            'content': user_message,
            'timestamp': timezone.now().isoformat()
        })
        
        # Try to extract field value from answer
        update_field_from_answer(upload, user_message)
        
        # Get AI response
        ai_response = get_ai_validation_response(upload, user_message)
        chat_history.append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': timezone.now().isoformat()
        })
        
        upload.validation_chat_history = chat_history
        upload.save()
        
        # Check if validation complete
        if check_validation_complete(upload):
            upload.status = 'complete'
            upload.save()
            # Create property
            property_obj = create_property_from_upload(upload)
            return render(request, 'properties/_import_success.html', {
                'property': property_obj,
                'upload': upload
            })
        
        # Return updated chat fragment
        return render(request, 'properties/_import_validation.html', {
            'upload': upload,
            'next_question': get_next_validation_question(upload),
            'chat_history': chat_history
        })
        
    except Exception as e:
        logger.error(f"Validation submit error: {e}", extra={
            'upload_id': upload_id,
            'user_id': request.user.id
        })
        return render(request, 'properties/_error_fragment.html', {
            'error': 'Error processing your answer. Please try again.'
        }, status=500)


@login_required
@require_POST
def import_complete(request: HttpRequest, upload_id: str) -> HttpResponse:
    """Manually trigger completion (if user wants to skip remaining validation)"""
    try:
        company = get_company(request)
        upload = get_object_or_404(PropertyUpload, id=upload_id, company=company)
        
        if upload.status == 'complete':
            property_obj = upload.property
            if property_obj:
                return render(request, 'properties/_import_success.html', {
                    'property': property_obj,
                    'upload': upload
                })
        
        # Create property even if validation incomplete
        property_obj = create_property_from_upload(upload)
        upload.status = 'complete'
        upload.property = property_obj
        upload.save()
        
        return render(request, 'properties/_import_success.html', {
            'property': property_obj,
            'upload': upload
        })
        
    except Exception as e:
        logger.error(f"Complete error: {e}", extra={
            'upload_id': upload_id,
            'user_id': request.user.id
        })
        return render(request, 'properties/_error_fragment.html', {
            'error': 'Error completing property creation.'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def import_success(request: HttpRequest, property_id: str) -> HttpResponse:
    """Return success fragment"""
    try:
        company = get_company(request)
        property_obj = get_object_or_404(Property, id=property_id, company=company)
        
        return render(request, 'properties/_import_success.html', {
            'property': property_obj
        })
    except Exception as e:
        logger.error(f"Success fragment error: {e}", extra={
            'property_id': property_id,
            'user_id': request.user.id
        })
        return render(request, 'properties/_error_fragment.html', {
            'error': 'Property not found.'
        }, status=404)


# Helper functions

def extract_property_data(text: str) -> dict:
    """Extract property data from text using OpenAI if available, fallback to regex"""
    # Try OpenAI extraction first if API key is available
    if settings.OPENAI_API_KEY:
        try:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            extraction_prompt = f"""Extract property information from this real estate listing text. Return ONLY a valid JSON object with no additional text or markdown.

Property Text:
{text[:2000]}

Return a JSON object with these fields (use null if not found):
{{
    "title": "property title or listing name",
    "price_amount": 3500,
    "city": "city name",
    "area": "area/neighborhood/barangay",
    "beds": 2,
    "baths": 2,
    "property_type": "condo/house/townhouse/etc",
    "description": "full description"
}}

Instructions:
- Extract price as integer (if "$3,500/month" extract 3500, if "$450k" extract 450000)
- City should be the main city (Makati, Manila, Quezon City, Taguig, etc.)
- Area is neighborhood/district (BGC, Rockwell, Ortigas, etc.)
- Beds and baths as integers
- Title should be concise and descriptive
- Return ONLY valid JSON, no markdown code blocks"""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a real estate data extraction assistant. Extract property information from text and return ONLY valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            json_str = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if json_str.startswith('```'):
                json_str = json_str.split('```')[1]
                if json_str.startswith('json'):
                    json_str = json_str[4:]
            json_str = json_str.strip()
            
            # Parse JSON
            extracted = json.loads(json_str)
            
            # Normalize and return
            data = {
                'title': extracted.get('title') or None,
                'price_amount': extracted.get('price_amount'),
                'city': extracted.get('city') or None,
                'area': extracted.get('area') or None,
                'beds': extracted.get('beds'),
                'baths': extracted.get('baths'),
            }
            
            # Clean up title
            if data['title'] and len(data['title']) > 255:
                data['title'] = data['title'][:255]
            
            logger.info(f"OpenAI extraction successful: {data}")
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"OpenAI returned invalid JSON: {e}, falling back to regex")
        except Exception as e:
            logger.warning(f"OpenAI extraction failed: {e}, falling back to regex")
    
    # Fallback to regex-based extraction
    data = {}
    
    # Extract price
    price_patterns = [
        r'\$([0-9,]+)',
        r'([0-9,]+)\s*(USD|dollars?|pesos?)',
        r'PHP\s*([0-9,]+)',
    ]
    for pattern in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                price_str = match.group(1).replace(',', '')
                if 'k' in match.group(0).lower():
                    data['price_amount'] = int(price_str) * 1000
                else:
                    data['price_amount'] = int(price_str)
                break
            except:
                continue
    
    # Extract beds
    beds_match = re.search(r'(\d+)\s*(bed|bedroom|br\b)', text, re.IGNORECASE)
    if beds_match:
        try:
            data['beds'] = int(beds_match.group(1))
        except:
            pass
    
    # Extract baths
    baths_match = re.search(r'(\d+)\s*(bath|bathroom|ba\b)', text, re.IGNORECASE)
    if baths_match:
        try:
            data['baths'] = int(baths_match.group(1))
        except:
            pass
    
    # Extract city (common Philippine cities)
    philippine_cities = ['Makati', 'Manila', 'Quezon City', 'Taguig', 'BGC', 'Pasig', 'Mandaluyong', 'Ortigas', 'Alabang', 'Rockwell']
    for city in philippine_cities:
        if city.lower() in text.lower():
            data['city'] = city
            break
    
    # Extract area/neighborhood
    area_keywords = ['BGC', 'Rockwell', 'Ortigas', 'Alabang', 'Makati CBD', 'Downtown']
    for area in area_keywords:
        if area.lower() in text.lower():
            data['area'] = area
            break
    
    # Extract title (first line or first sentence)
    lines = text.split('\n')
    if lines:
        first_line = lines[0].strip()
        if len(first_line) > 10 and len(first_line) < 100:
            data['title'] = first_line
        else:
            # Try first sentence
            sentences = text.split('.')
            if sentences:
                data['title'] = sentences[0].strip()[:100]
    
    return data


def start_light_validation(upload: PropertyUpload):
    """Run fast validation check and update status"""
    try:
        # Build property context
        property_context = {
            'title': upload.title or '',
            'description': upload.description or '',
            'price': upload.price_amount or 0,
            'city': upload.city or '',
            'area': upload.area or '',
            'beds': upload.beds or 0,
            'baths': upload.baths or 0,
        }
        
        # Check for critical missing fields
        missing_fields = []
        critical_fields = {
            'title': 'Property Title',
            'price_amount': 'Price',
            'city': 'City',
        }
        
        for field, label in critical_fields.items():
            if not getattr(upload, field, None):
                missing_fields.append(label)
        
        # Initialize validation result
        upload.ai_validation_result = {
            'property_identification': 'complete' if upload.title else 'missing',
            'location_details': 'partial' if upload.city else 'missing',
            'financial_info': 'complete' if upload.price_amount else 'missing',
        }
        upload.missing_fields = missing_fields
        
        # If no critical fields missing, mark as complete
        if not missing_fields:
            upload.status = 'complete'
        else:
            upload.status = 'validation'
        
        upload.save()
        
        # Emit job for deep validation (async)
        if upload.company:
            # JobTask.objects.create(
            #     company=upload.company,
            #     kind='property_validation_deep',
            #     payload={'upload_id': str(upload.id)},
            #     status='pending'
            # )
            pass
        
    except Exception as e:
        logger.error(f"Light validation error: {e}", extra={
            'upload_id': upload.id
        })
        # Don't fail - just mark as validation
        upload.status = 'validation'
        upload.save()


def get_next_validation_question(upload: PropertyUpload) -> dict:
    """Get the next question to ask"""
    missing_fields = upload.missing_fields or []
    
    if not missing_fields:
        return {
            'field': None,
            'question': 'All required information has been collected!',
            'example': ''
        }
    
    # Get first missing field
    next_field = missing_fields[0]
    
    questions = {
        'Property Title': {
            'question': 'What is the property title or listing name? (e.g., "Luxury 2BR Condo in BGC")',
            'example': 'Modern 2BR Condo with City Views'
        },
        'Price': {
            'question': 'What is the monthly rent or purchase price? (e.g., "$3,500/month" or "$450,000")',
            'example': '$3,500'
        },
        'City': {
            'question': 'What city is this property located in?',
            'example': 'Makati'
        },
        'Full Street Address': {
            'question': 'What is the full street address? (e.g., "15th Floor, One Parkade, 16th Avenue, Fort Bonifacio, Taguig City, 1634")',
            'example': '123 Main Street, Barangay, City, ZIP Code'
        },
    }
    
    return questions.get(next_field, {
        'field': next_field,
        'question': f'Please provide: {next_field}',
        'example': ''
    })


def update_field_from_answer(upload: PropertyUpload, answer: str):
    """Try to extract and update field from user answer"""
    missing_fields = upload.missing_fields or []
    if not missing_fields:
        return
    
    field = missing_fields[0]
    
    # Update field based on answer
    if 'title' in field.lower() or 'property title' in field.lower():
        upload.title = answer.strip()[:255]
        upload.missing_fields = [f for f in missing_fields if f != field]
    elif 'price' in field.lower():
        # Extract price
        price_match = re.search(r'\$?([0-9,]+)', answer)
        if price_match:
            try:
                upload.price_amount = int(price_match.group(1).replace(',', ''))
                upload.missing_fields = [f for f in missing_fields if f != field]
            except:
                pass
    elif 'city' in field.lower():
        upload.city = answer.strip()[:64]
        upload.missing_fields = [f for f in missing_fields if f != field]
    elif 'address' in field.lower():
        # Store in description or create address field
        if not upload.description:
            upload.description = f"Address: {answer.strip()}\n\n"
        else:
            upload.description = f"Address: {answer.strip()}\n\n{upload.description}"
        upload.missing_fields = [f for f in missing_fields if f != field]
    
    upload.save()


def get_ai_validation_response(upload: PropertyUpload, user_message: str) -> str:
    """Get AI response for validation chat"""
    # Simple rule-based for now (can be enhanced with OpenAI)
    missing_fields = upload.missing_fields or []
    
    if not missing_fields:
        return "Perfect! All required information has been collected. Your property listing is being finalized..."
    
    next_field = missing_fields[0] if missing_fields else None
    
    if next_field:
        return f"Thank you! I've recorded that information. Now I need: {next_field}. {get_next_validation_question(upload).get('example', '')}"
    
    return "Thank you for providing that information. Is there anything else you'd like to add about this property?"


def check_validation_complete(upload: PropertyUpload) -> bool:
    """Check if validation is complete"""
    missing_fields = upload.missing_fields or []
    critical_fields = ['Property Title', 'Price', 'City']
    
    return not any(field in missing_fields for field in critical_fields)


def enrich_property_with_ai(upload: PropertyUpload):
    """Enrich PropertyUpload with AI-generated details"""
    if not settings.OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured, skipping enrichment")
        return
    
    try:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build property context
        property_context = {
            'title': upload.title or 'Untitled Property',
            'description': upload.description or '',
            'price': upload.price_amount or 0,
            'city': upload.city or '',
            'area': upload.area or '',
            'beds': upload.beds or 0,
            'baths': upload.baths or 0,
        }
        
        # Create enrichment prompt
        enrichment_prompt = f"""You are a real estate data enrichment assistant. Given the following property information, generate additional details that would be valuable for a property listing.

Current Property Information:
- Title: {property_context['title']}
- Description: {property_context['description'][:500]}
- Price: ${property_context['price']}
- City: {property_context['city']}
- Area: {property_context['area']}
- Bedrooms: {property_context['beds']}
- Bathrooms: {property_context['baths']}

Please enrich this property listing by:
1. Improving the description if it's generic or short (make it appealing and detailed)
2. Adding property features (amenities, facilities, nearby attractions)
3. Suggesting property type if not clear
4. Adding any missing details that would help buyers/renters

Return ONLY a valid JSON object with these fields:
{{
    "enhanced_description": "detailed, appealing property description",
    "property_features": ["feature1", "feature2", "feature3"],
    "property_type": "condo/house/townhouse/etc",
    "nearby_amenities": ["amenity1", "amenity2"],
    "selling_points": ["point1", "point2"]
}}

Return ONLY valid JSON, no markdown code blocks."""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a real estate data enrichment assistant. Generate detailed property information in JSON format."},
                {"role": "user", "content": enrichment_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        json_str = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if json_str.startswith('```'):
            json_str = json_str.split('```')[1]
            if json_str.startswith('json'):
                json_str = json_str[4:]
        json_str = json_str.strip()
        
        # Parse JSON
        enriched_data = json.loads(json_str)
        
        # Update PropertyUpload with enriched data
        if enriched_data.get('enhanced_description'):
            # Merge with existing description
            if upload.description:
                upload.description = f"{upload.description}\n\n{enriched_data['enhanced_description']}"
            else:
                upload.description = enriched_data['enhanced_description']
        
        # Store enrichment data in ai_validation_result
        upload.ai_validation_result = {
            **upload.ai_validation_result,
            'ai_enrichment': enriched_data,
            'enriched_at': timezone.now().isoformat()
        }
        
        # Add features to description
        if enriched_data.get('property_features'):
            features_text = "\n\nFeatures:\n" + "\n".join([f"• {f}" for f in enriched_data['property_features'][:10]])
            upload.description += features_text
        
        upload.save()
        
        logger.info(f"AI enrichment completed for upload {upload.id}")
        
    except json.JSONDecodeError as e:
        logger.error(f"AI enrichment JSON parse error: {e}")
    except Exception as e:
        logger.error(f"AI enrichment error: {e}")


def create_property_from_upload(upload: PropertyUpload) -> Property:
    """Create Property object from validated upload"""
    from django.utils.text import slugify
    
    # Generate unique slug
    base_slug = slugify(upload.title or 'property')
    slug = base_slug
    counter = 1
    
    while Property.objects.filter(slug=slug, company=upload.company).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Consolidate description
    description = upload.description or ''
    if upload.validation_chat_history:
        # Add chat history summary
        chat_summary = "\n\nAdditional Information:\n"
        for msg in upload.validation_chat_history[-5:]:  # Last 5 messages
            if msg.get('role') == 'user':
                chat_summary += f"- {msg.get('content', '')}\n"
        description += chat_summary
    
    # Create Property
    property_obj = Property.objects.create(
        company=upload.company,
        title=upload.title or 'Untitled Property',
        description=description,
        price_amount=upload.price_amount or 0,
        city=upload.city or '',
        area=upload.area or '',
        beds=upload.beds or 1,
        baths=upload.baths or 1,
        slug=slug,
        hero_image=upload.hero_image or '',
        badges="AI-Validated"
    )
    
    # Link PropertyUpload to Property
    upload.property = property_obj
    upload.status = 'complete'
    upload.save()
    
    # Send webhooks
    try:
        from .webhook import send_property_listing_webhook
        property_data = {
            "id": str(property_obj.id),
            "slug": property_obj.slug,
            "title": property_obj.title,
            "description": property_obj.description,
            "price_amount": property_obj.price_amount,
            "city": property_obj.city,
            "area": property_obj.area,
            "beds": property_obj.beds,
            "baths": property_obj.baths,
            "hero_image": property_obj.hero_image,
            "created_at": property_obj.created_at.isoformat(),
            "upload_id": str(upload.id),
            "timestamp": timezone.now().isoformat(),
        }
        send_property_listing_webhook(property_data)
    except Exception as e:
        logger.error(f"Webhook error: {e}", extra={
            'property_id': property_obj.id
        })
    
    return property_obj

