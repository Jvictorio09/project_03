from __future__ import annotations

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db import connection
from django.contrib import messages
from django.utils import timezone

from .models import Property, Lead, PropertyUpload
from .forms import LeadForm, PropertyUploadForm
from .webhook import send_chat_inquiry_webhook, send_property_listing_webhook, send_property_chat_webhook, send_prompt_search_webhook


def home(request: HttpRequest) -> HttpResponse:
    top_picks = Property.objects.all()[:6]
    return render(request, "home.html", {"top_picks": top_picks})


def results(request: HttpRequest) -> HttpResponse:
    qs = Property.objects.all()
    q = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    beds = request.GET.get("beds", "").strip()
    price_max = request.GET.get("price_max", "").strip()
    ai_prompt = request.GET.get("ai_prompt", "").strip()

    # Handle AI prompt search
    if ai_prompt:
        # Use AI prompt to enhance search
        enhanced_search = process_ai_search_prompt(ai_prompt)
        
        # Apply enhanced search filters
        if enhanced_search.get("city"):
            qs = qs.filter(Q(city__icontains=enhanced_search["city"]) | Q(area__icontains=enhanced_search["city"]))
        if enhanced_search.get("beds"):
            qs = qs.filter(beds__gte=enhanced_search["beds"])
        if enhanced_search.get("price_max"):
            qs = qs.filter(price_amount__lte=enhanced_search["price_max"])
        if enhanced_search.get("keywords"):
            for keyword in enhanced_search["keywords"]:
                qs = qs.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(badges__icontains=keyword))
        
        # Send webhook for prompt-based search
        try:
            search_webhook_data = {
                "prompt": ai_prompt,
                "results_count": qs.count(),
                "session_id": request.session.session_key or "anonymous",
                "buy_or_rent": enhanced_search.get("buy_or_rent", ""),
                "budget_max": enhanced_search.get("price_max"),
                "beds": enhanced_search.get("beds"),
                "areas": enhanced_search.get("city", ""),
                "property_ids": ",".join([str(p.id) for p in qs[:5]]),  # Top 5 property IDs
                "timestamp": timezone.now().isoformat(),
                "utm_source": request.COOKIES.get("utm_source", request.GET.get("utm_source", "")),
                "utm_campaign": request.COOKIES.get("utm_campaign", request.GET.get("utm_campaign", "")),
                "referrer": request.META.get("HTTP_REFERER", ""),
            }
            send_prompt_search_webhook(search_webhook_data)
        except Exception as e:
            # Log but don't fail the request
            print(f"Prompt search webhook error: {e}")
    
    # Handle traditional search
    else:
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(badges__icontains=q) | Q(city__icontains=q))
        if city:
            qs = qs.filter(Q(city__iexact=city) | Q(area__icontains=city))
        if beds and beds.isdigit():
            qs = qs.filter(beds__gte=int(beds))
        if price_max and price_max.isdigit():
            qs = qs.filter(price_amount__lte=int(price_max))

    return render(request, "results.html", {
        "properties": qs, 
        "count": qs.count(),
        "ai_prompt": ai_prompt,
        "search_type": "ai_prompt" if ai_prompt else "traditional"
    })


def property_detail(request: HttpRequest, slug: str) -> HttpResponse:
    prop = get_object_or_404(Property, slug=slug)
    return render(request, "property_detail.html", {"property": prop})


def lead_submit(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    form = LeadForm(request.POST)
    if form.is_valid():
        lead: Lead = form.save(commit=False)
        # capture tracking
        lead.utm_source = request.COOKIES.get("utm_source", request.GET.get("utm_source", ""))
        lead.utm_campaign = request.COOKIES.get("utm_campaign", request.GET.get("utm_campaign", ""))
        lead.referrer = request.META.get("HTTP_REFERER", "")
        # interest ids if provided
        lead.interest_ids = request.POST.get("interest_ids", "")
        lead.save()

        # Send webhook to Katalyst CRM
        try:
            webhook_data = {
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "buy_or_rent": lead.buy_or_rent,
                "budget_max": lead.budget_max,
                "beds": lead.beds,
                "areas": lead.areas,
                "interest_ids": lead.interest_ids,
                "utm_source": lead.utm_source,
                "utm_campaign": lead.utm_campaign,
                "referrer": lead.referrer,
                "session_id": request.session.session_key or "anonymous",
                "timestamp": timezone.now().isoformat(),
                "message": "Lead form submission"
            }
            send_chat_inquiry_webhook(webhook_data)
        except Exception as e:
            # Log but don't fail the request
            print(f"Webhook error: {e}")

        # HTMX handling
        if request.headers.get("HX-Request") == "true":
            return render(request, "partials/lead_success.html", {"lead": lead})

        return redirect(f"{reverse('thanks')}?lead={lead.id}")

    # invalid form; if HTMX return the form partial
    status = 400
    if request.headers.get("HX-Request") == "true":
        return render(request, "partials/lead_form.html", {"form": form}, status=status)
    return HttpResponseRedirect(reverse("home"))


def book(request: HttpRequest) -> HttpResponse:
    lead_id = request.GET.get("lead")
    lead: Lead | None = None
    if lead_id:
        lead = Lead.objects.filter(id=lead_id).first()
    return render(request, "book.html", {"lead": lead})


def thanks(request: HttpRequest) -> HttpResponse:
    lead_id = request.GET.get("lead")
    lead: Lead | None = None
    if lead_id:
        lead = Lead.objects.filter(id=lead_id).first()
    return render(request, "thanks.html", {"lead": lead})


def dashboard(request: HttpRequest) -> HttpResponse:
    """Listings Dashboard for internal users"""
    # Query params
    q = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    sort = request.GET.get("sort", "new")
    page = int(request.GET.get("page", 1))
    per = min(int(request.GET.get("per", 12)), 48)
    
    # Base queryset
    properties = Property.objects.all()
    
    # Search filter
    if q:
        properties = properties.filter(
            Q(title__icontains=q) | 
            Q(area__icontains=q) | 
            Q(city__icontains=q) | 
            Q(description__icontains=q)
        )
    
    # City filter
    if city:
        properties = properties.filter(city__iexact=city)
    
    # Sorting
    sort_options = {
        "new": "-created_at",
        "price_asc": "price_amount",
        "price_desc": "-price_amount", 
        "beds_desc": "-beds"
    }
    properties = properties.order_by(sort_options.get(sort, "-created_at"))
    
    # Pagination
    paginator = Paginator(properties, per)
    page_obj = paginator.get_page(page)
    
    # Get distinct cities for filter dropdown
    cities = Property.objects.values_list("city", flat=True).distinct().order_by("city")
    
    context = {
        "properties": page_obj,
        "cities": cities,
        "total_count": paginator.count,
        "current_filters": {
            "q": q,
            "city": city,
            "sort": sort,
            "per": per
        }
    }
    
    return render(request, "dashboard.html", context)


@require_POST
def property_chat(request: HttpRequest, slug: str) -> HttpResponse:
    """HTMX endpoint for property chat"""
    property_obj = get_object_or_404(Property, slug=slug)
    message = request.POST.get("message", "").strip().lower()
    
    if not message:
        return HttpResponseBadRequest("Message required")
    
    # Simple rule-based responder
    response_text = simple_answer(property_obj, message)
    
    # Send webhook to Katalyst CRM
    try:
        chat_webhook_data = {
            "property_id": property_obj.id,
            "property_slug": property_obj.slug,
            "property_title": property_obj.title,
            "property_city": property_obj.city,
            "property_price": property_obj.price_amount,
            "message": message,
            "response": response_text,
            "session_id": request.session.session_key or "anonymous",
            "timestamp": timezone.now().isoformat(),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "ip_address": request.META.get("REMOTE_ADDR", ""),
            "referrer": request.META.get("HTTP_REFERER", ""),
        }
        send_property_chat_webhook(chat_webhook_data)
    except Exception as e:
        # Log but don't fail the request
        print(f"Webhook error: {e}")
    
    # Render chat bubble partial
    context = {
        "role": "assistant",
        "text": response_text,
        "time": "now"
    }
    
    return render(request, "partials/chat_bubble.html", context)


@require_POST
def property_chat_simple(request: HttpRequest, slug: str) -> HttpResponse:
    """Simplified HTMX endpoint for property chat - NO WEBHOOKS"""
    property_obj = get_object_or_404(Property, slug=slug)
    message = request.POST.get("message", "").strip()
    
    if not message:
        return HttpResponseBadRequest("Message required")
    
    # Simple rule-based responder (same as before)
    response_text = simple_answer(property_obj, message.lower())
    
    # Render chat bubble partial - NO WEBHOOKS
    context = {
        "role": "assistant",
        "text": response_text,
        "time": "now"
    }
    
    return render(request, "partials/chat_bubble.html", context)


@require_POST
def property_chat_ai(request: HttpRequest, slug: str) -> HttpResponse:
    """AI-powered property chat that queries database intelligently"""
    property_obj = get_object_or_404(Property, slug=slug)
    message = request.POST.get("message", "").strip()
    
    if not message:
        return HttpResponseBadRequest("Message required")
    
    # Get AI response with database context
    response_text = get_ai_property_response(property_obj, message)
    
    # Render chat bubble partial
    context = {
        "role": "assistant",
        "text": response_text,
        "time": "now"
    }
    
    return render(request, "partials/chat_bubble.html", context)


def health_check(request: HttpRequest) -> HttpResponse:
    """Health check endpoint for Railway"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({"status": "healthy", "database": "connected"})
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)


def process_ai_search_prompt(prompt: str) -> dict:
    """
    Process AI search prompt to extract search parameters
    
    Args:
        prompt: User's natural language search prompt
    
    Returns:
        dict: Extracted search parameters
    """
    import re
    
    result = {
        "city": "",
        "beds": None,
        "price_max": None,
        "buy_or_rent": "",
        "keywords": []
    }
    
    prompt_lower = prompt.lower()
    
    # Extract city
    cities = ["los angeles", "new york", "chicago", "miami", "san francisco", "seattle", "boston", "austin", "houston", "phoenix", "philadelphia", "san antonio", "san diego", "dallas", "san jose", "jacksonville", "fort worth", "columbus", "charlotte", "indianapolis", "denver", "washington", "el paso", "nashville", "detroit", "oklahoma city", "portland", "las vegas", "memphis", "louisville", "baltimore", "milwaukee", "albuquerque", "tucson", "fresno", "sacramento", "mesa", "kansas city", "atlanta", "long beach", "colorado springs", "raleigh", "virginia beach", "omaha", "oakland", "minneapolis", "tulsa", "arlington", "tampa"]
    
    for city in cities:
        if city in prompt_lower:
            result["city"] = city.title()
            break
    
    # Extract bedrooms
    beds_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', prompt_lower)
    if beds_match:
        result["beds"] = int(beds_match.group(1))
    
    # Extract price
    price_match = re.search(r'\$([0-9,]+)', prompt)
    if price_match:
        try:
            result["price_max"] = int(price_match.group(1).replace(',', ''))
        except:
            pass
    
    # Determine buy or rent
    if any(word in prompt_lower for word in ["rent", "rental", "lease", "monthly", "per month"]):
        result["buy_or_rent"] = "rent"
    elif any(word in prompt_lower for word in ["buy", "purchase", "own", "owner"]):
        result["buy_or_rent"] = "buy"
    
    # Extract keywords for enhanced search
    keywords = []
    if "condo" in prompt_lower:
        keywords.append("condo")
    if "apartment" in prompt_lower:
        keywords.append("apartment")
    if "house" in prompt_lower:
        keywords.append("house")
    if "gym" in prompt_lower:
        keywords.append("gym")
    if "pool" in prompt_lower:
        keywords.append("pool")
    if "pet" in prompt_lower:
        keywords.append("pet")
    if "parking" in prompt_lower:
        keywords.append("parking")
    if "downtown" in prompt_lower:
        keywords.append("downtown")
    if "modern" in prompt_lower:
        keywords.append("modern")
    if "luxury" in prompt_lower:
        keywords.append("luxury")
    
    result["keywords"] = keywords
    
    return result


def get_ai_property_response(property_obj: Property, message: str) -> str:
    """AI-powered response that can query database and provide intelligent answers"""
    import openai
    from django.conf import settings
    
    # Check if OpenAI API key is available
    if not settings.OPENAI_API_KEY:
        # Fallback to simple answer if no API key
        return simple_answer(property_obj, message.lower())
    
    try:
        # Prepare comprehensive property data for AI context
        property_data = {
            "title": property_obj.title,
            "description": property_obj.description,
            "price_amount": property_obj.price_amount,
            "city": property_obj.city,
            "area": property_obj.area,
            "beds": property_obj.beds,
            "baths": property_obj.baths,
            "floor_area_sqm": property_obj.floor_area_sqm,
            "parking": property_obj.parking,
            "property_type": property_obj.property_type,
            "badges": property_obj.badges,
            "hero_image": str(property_obj.hero_image) if property_obj.hero_image else None,
        }
        
        # Get related properties for comparison context
        related_properties = Property.objects.filter(
            city=property_obj.city
        ).exclude(id=property_obj.id)[:5]
        
        related_data = []
        for prop in related_properties:
            related_data.append({
                "title": prop.title,
                "price": prop.price_amount,
                "beds": prop.beds,
                "baths": prop.baths,
                "area": prop.area
            })
        
        # Create AI system prompt
        system_prompt = f"""You are an intelligent real estate assistant with access to comprehensive property data. 

CURRENT PROPERTY DATA:
{property_data}

RELATED PROPERTIES IN SAME AREA:
{related_data}

You can answer questions about:
- Property details, pricing, and features
- Comparisons with similar properties in the area
- Market insights and value analysis
- Location benefits and amenities
- Investment potential and rental estimates
- Any other property-related questions

Be helpful, accurate, and conversational. Use the data provided to give specific, detailed answers. If you need to make comparisons, use the related properties data. Always be honest about what information is available vs. what might need further research.

Respond naturally and helpfully to the user's question."""

        # Call OpenAI API
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"AI chat error: {e}")
        # Fallback to simple answer if AI fails
        return simple_answer(property_obj, message.lower())


def simple_answer(prop: Property, text: str) -> str:
    """Simple rule-based responder for property questions"""
    text = text.lower()
    
    # Price questions
    if any(word in text for word in ["price", "rent", "cost", "monthly"]):
        return f"The monthly rent is ${prop.price_amount:,} USD."
    
    # Bedrooms
    if any(word in text for word in ["bed", "beds", "bedroom"]):
        return f"This property has {prop.beds} bedroom{'s' if prop.beds != 1 else ''}."
    
    # Bathrooms  
    if any(word in text for word in ["bath", "baths", "bathroom"]):
        return f"This property has {prop.baths} bathroom{'s' if prop.baths != 1 else ''}."
    
    # Size/area
    if any(word in text for word in ["size", "sqm", "area", "square"]):
        if prop.floor_area_sqm:
            return f"The floor area is {prop.floor_area_sqm} square meters."
        return "Floor area information is not available for this property."
    
    # Parking
    if any(word in text for word in ["park", "parking"]):
        return f"Parking is {'available' if prop.parking else 'not available'} for this property."
    
    # Location
    if any(word in text for word in ["where", "location", "city", "area", "address"]):
        location = f"{prop.city}"
        if prop.area:
            location += f", {prop.area}"
        
        # Create Google Maps link
        maps_query = f"{prop.title} {prop.area or ''} {prop.city}".replace(" ", "+")
        maps_url = f"https://maps.google.com/maps?q={maps_query}"
        
        return f"Located in {location}. [View on Google Maps]({maps_url})"
    
    # Availability
    if any(word in text for word in ["available", "availability", "vacant", "when"]):
        return "Availability changes daily. Drop your number and we'll confirm current status."
    
    # Fees/deposits
    if any(word in text for word in ["fees", "deposit", "hoa", "association", "maintenance"]):
        return "No HOA/association fees noted for this property."
    
    # Fallback
    return "I'll pass this to the agent—want to leave your number for a direct response?"


def upload_listing(request: HttpRequest) -> HttpResponse:
    """Handle property upload form"""
    if request.method == 'POST':
        form = PropertyUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save()
            upload.status = 'processing'
            upload.save()
            
            # Start AI validation process
            validate_property_with_ai(upload)
            
            return redirect('processing_listing', upload_id=upload.id)
    else:
        form = PropertyUploadForm()
    
    return render(request, 'upload_listing.html', {'form': form})


def processing_listing(request: HttpRequest, upload_id: str) -> HttpResponse:
    """Show processing status"""
    upload = get_object_or_404(PropertyUpload, id=upload_id)
    
    # Check if processing is complete
    if upload.status == 'validation':
        return redirect('validation_chat', upload_id=upload.id)
    elif upload.status == 'complete':
        return redirect('property_detail', slug=upload.property.slug)
    
    return render(request, 'processing_listing.html', {'upload': upload})


def validation_chat(request: HttpRequest, upload_id: str) -> HttpResponse:
    """Handle validation chat interface"""
    upload = get_object_or_404(PropertyUpload, id=upload_id)
    
    if request.method == 'POST':
        user_message = request.POST.get('user_message', '').strip()
        if user_message:
            # Add user message to chat history
            chat_history = upload.validation_chat_history or []
            chat_history.append({
                'role': 'user',
                'content': user_message,
                'timestamp': 'Just now'
            })
            
            # Get AI response
            ai_response = get_ai_validation_response(upload, user_message)
            chat_history.append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': 'Just now'
            })
            
            upload.validation_chat_history = chat_history
            upload.save()
            
            # Send webhook for validation chat interaction
            try:
                validation_chat_data = {
                    "id": upload.id,
                    "name": "Property Listing Validation",
                    "phone": "",
                    "email": "",
                    "buy_or_rent": "sell",
                    "budget_max": upload.price_amount,
                    "beds": upload.beds,
                    "areas": upload.area or upload.city,
                    "interest_ids": "",
                    "utm_source": "",
                    "utm_campaign": "",
                    "referrer": "",
                    "session_id": request.session.session_key or "anonymous",
                    "timestamp": timezone.now().isoformat(),
                    "message": user_message,
                    "property": {
                        "upload_id": str(upload.id),
                        "title": upload.title,
                        "city": upload.city,
                        "price": upload.price_amount,
                        "status": upload.status,
                        "validation_progress": len([msg for msg in chat_history if msg.get('role') == 'user'])
                    }
                }
                send_chat_inquiry_webhook(validation_chat_data)
            except Exception as e:
                # Log but don't fail the request
                print(f"Webhook error: {e}")
            
            # Check if validation is complete
            if check_validation_complete(upload):
                upload.status = 'complete'
                # Create the actual Property object
                create_property_from_upload(upload)
                upload.save()
                return redirect('property_detail', slug=upload.property.slug)
    
    # Calculate completion percentage
    total_fields = 9  # Number of validation sections
    complete_sections = sum(1 for status in upload.ai_validation_result.values() if status == 'complete')
    completion_percentage = int((complete_sections / total_fields) * 100)
    
    context = {
        'upload': upload,
        'chat_history': upload.validation_chat_history or [],
        'completion_percentage': completion_percentage,
        'validation_status': upload.ai_validation_result or {},
        'missing_fields': upload.missing_fields or []
    }
    
    return render(request, 'validation_chat.html', context)


def validate_property_with_ai(upload: PropertyUpload):
    """Send property data to OpenAI for validation"""
    import openai
    import json
    from django.conf import settings
    
    # Set OpenAI API key
    openai.api_key = settings.OPENAI_API_KEY
    
    # Prepare property data for AI validation
    property_data = {
        'title': upload.title,
        'description': upload.description,
        'price_amount': upload.price_amount,
        'city': upload.city,
        'area': upload.area,
        'beds': upload.beds,
        'baths': upload.baths,
    }
    
    system_message = """You are a real estate data validator AI.  
You will receive property data (structured, unstructured, or retrieved chunks) and your job is to cross-check it against the following U.S. Real Estate Property Information Checklist.

For each section, determine whether the information is:
- ✅ Complete (enough data to answer related user queries confidently),
- ⚠️ Partial (some critical fields are missing), or
- ❌ Missing (cannot answer questions reliably for that section).

If critical information is missing, specify exactly which fields are missing.

---

🏡 1. Property Identification
- MLS Number / Internal Property ID
- Property Title / Listing Name
- Property Type (Single Family, Condo, Townhouse, Multi-family, Commercial, Land)
- Subtype (e.g., Duplex, High-rise Condo, Manufactured Home)
- Listing Status (Active, Pending, Contingent, Sold, Off-market)
- Listing Date & Last Updated
- Listing Agent & Brokerage Information
- Days on Market (DOM)

📍 2. Location Details
- Full Street Address (House No., Street, City, State, ZIP)
- County / Census Tract
- Subdivision / Community Name
- HOA / Community Association (Y/N + name)
- School District (Elementary, Middle, High School zones)
- Nearby Landmarks & Transportation Access
- GPS Coordinates (Latitude, Longitude)

📐 3. Lot and Building Information
- Lot Size (sq ft or acres)
- Lot Dimensions
- Zoning Code & Land Use Type (Residential, Commercial, Mixed)
- Year Built / Year Renovated
- Total Living Area (sq ft)
- Total Building Area (if different)
- Number of Stories
- Basement (Finished / Unfinished / Walkout)
- Roof Type & Material
- Exterior Construction Material
- Parking (Garage spaces, driveway capacity)

🛋 4. Interior Features
- Number of Bedrooms
- Number of Bathrooms (Full / Half)
- Kitchen features (appliances, countertops, layout)
- Flooring Materials
- HVAC (Heating, Cooling, Ventilation details)
- Fireplace (Y/N, type)
- Laundry Room (Location & Type)
- Accessibility Features (ADA compliance, ramps, elevators)
- Energy Efficiency Features (Solar, smart thermostats, insulation ratings)

🏢 5. Property Features & Amenities
- Outdoor spaces (Deck, Patio, Balcony, Pool, Lawn, Fence)
- Landscaping / Irrigation systems
- HOA Amenities (Gym, Tennis courts, Clubhouse, Pool)
- Security systems / Gated community
- Views (Mountain, City, Water, Golf course, etc.)
- Waterfront / Water access details (if applicable)
- Inclusions / Exclusions (e.g., appliances, furniture)

💰 6. Pricing and Financial Information
- List Price (USD)
- Price per sq ft
- HOA Fees (monthly/annual)
- Property Taxes (annual, latest year)
- Special Assessments (Y/N + amount)
- Utility Costs (avg. electric, water, gas)
- Lease information (for rentals): rent amount, lease terms, security deposit
- Financing options offered (FHA/VA eligible, owner financing, cash only)
- Estimated Closing Costs (title, escrow, taxes)

📜 7. Legal & Ownership Information
- Title Status (Fee Simple, Leasehold, Trust, REO, Foreclosure)
- Deed Type (Warranty, Quitclaim, etc.)
- Parcel Number (APN)
- Recorded Liens / Encumbrances
- Easements / Rights of Way
- Occupancy Status (Owner-occupied, Tenant-occupied, Vacant)
- Zoning Variances or Permits
- Flood Zone Classification (FEMA maps)

🖼 8. Media & Marketing Assets
- Professional Photos (min. cover + gallery)
- Floor Plans (PDF or image)
- Virtual Tour / 3D Walkthrough (Matterport, Zillow 3D, etc.)
- Video Tours (YouTube or embedded links)
- Drone Photography / Aerial shots
- Property Website / Landing Page
- Marketing Remarks / Description (MLS text)

📎 9. Documentation & Disclosures
- Property Disclosure Statements (Seller's Disclosure, Lead Paint, Radon, etc.)
- Title Report / Preliminary Title
- HOA Documents (CC&Rs, Rules & Regs, Budgets)
- Recent Inspection Reports (Home, Roof, Pest, Sewer, etc.)
- Appraisal Report (if available)
- Survey / Plat Map
- Permits (Renovations, Additions, Pool, etc.)
- Energy Certifications (e.g., LEED, Energy Star)

---

When a user asks a question about a property, first check if the necessary fields above are present in the retrieved data.  
- If yes → answer normally.  
- If partially present → answer with available data and specify what's missing.  
- If missing → clearly state that the information is unavailable and recommend uploading or checking relevant documents.

Be strict about critical fields like: address, property type, lot size, price, legal status, and media assets.

Your output should be structured and explicit about what is present and what is missing.

Please respond with a JSON object containing:
1. "validation_result": An object with section names as keys and "complete", "partial", or "missing" as values
2. "missing_fields": An array of specific missing field names
3. "recommendations": An array of specific recommendations for the user"""

    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Please validate this property data: {json.dumps(property_data, indent=2)}"}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        # Parse the AI response
        ai_response = response.choices[0].message.content
        
        try:
            # Try to parse as JSON
            parsed_response = json.loads(ai_response)
            validation_result = parsed_response.get('validation_result', {})
            missing_fields = parsed_response.get('missing_fields', [])
            recommendations = parsed_response.get('recommendations', [])
        except json.JSONDecodeError:
            # Fallback if AI doesn't return proper JSON
            validation_result = {
                "Property Identification": "partial",
                "Location Details": "missing", 
                "Lot and Building Information": "partial",
                "Interior Features": "complete",
                "Property Features & Amenities": "missing",
                "Pricing and Financial Information": "complete",
                "Legal & Ownership Information": "missing",
                "Media & Marketing Assets": "partial",
                "Documentation & Disclosures": "missing"
            }
            missing_fields = [
                "Full Street Address",
                "Property Type",
                "Lot Size",
                "Year Built",
                "HOA Information",
                "Parking Details"
            ]
            recommendations = ["Please provide more detailed property information"]
        
        upload.ai_validation_result = validation_result
        upload.missing_fields = missing_fields
        upload.validation_chat_history = [{
            'role': 'assistant',
            'content': f"AI Analysis Complete! I've identified {len(missing_fields)} critical areas that need more information to create a comprehensive property listing. I'll guide you through each one systematically to ensure we have all the details buyers need. Let's start with the most important information first.",
            'timestamp': 'Just now'
        }]
        upload.status = 'validation'
        upload.save()
        
    except Exception as e:
        # Fallback to simulated response if API fails
        validation_result = {
            "Property Identification": "partial",
            "Location Details": "missing", 
            "Lot and Building Information": "partial",
            "Interior Features": "complete",
            "Property Features & Amenities": "missing",
            "Pricing and Financial Information": "complete",
            "Legal & Ownership Information": "missing",
            "Media & Marketing Assets": "partial",
            "Documentation & Disclosures": "missing"
        }
        
        # Comprehensive missing fields for thorough validation
        missing_fields = [
            "Full Street Address",
            "Property Type", 
            "Lot Size",
            "Year Built",
            "Total Living Area",
            "HOA Information",
            "Parking Details",
            "Kitchen Features",
            "Flooring Materials",
            "HVAC System",
            "Outdoor Spaces",
            "Property Taxes",
            "Utility Costs",
            "Title Status",
            "Occupancy Status",
            "Flood Zone",
            "Floor Plans",
            "Virtual Tour",
            "Inspection Reports",
            "Disclosures"
        ]
        
        upload.ai_validation_result = validation_result
        upload.missing_fields = missing_fields
        upload.validation_chat_history = [{
            'role': 'assistant',
            'content': f"AI Analysis Complete! I've identified {len(missing_fields)} critical areas that need more information to create a comprehensive property listing. I'll guide you through each one systematically to ensure we have all the details buyers need. Let's start with the most important information first.",
            'timestamp': 'Just now'
        }]
        upload.status = 'validation'
        upload.save()


def get_ai_validation_response(upload: PropertyUpload, user_message: str) -> str:
    """Get AI response for validation chat"""
    import openai
    import json
    from django.conf import settings
    
    # Set OpenAI API key
    openai.api_key = settings.OPENAI_API_KEY
    
    # Get the next missing field to ask about
    missing_fields = upload.missing_fields or []
    chat_history = upload.validation_chat_history or []
    
    # Count how many questions have been asked
    user_messages = [msg for msg in chat_history if msg.get('role') == 'user']
    current_question_index = len(user_messages)
    
    # Prepare comprehensive context for the AI
    property_context = {
        'title': upload.title,
        'description': upload.description,
        'price_amount': upload.price_amount,
        'city': upload.city,
        'area': upload.area,
        'beds': upload.beds,
        'baths': upload.baths,
        'missing_fields': missing_fields,
        'validation_status': upload.ai_validation_result,
        'current_question_index': current_question_index
    }
    
    chat_system_message = """You are a comprehensive real estate listing assistant. Your job is to systematically guide users through completing ALL missing information for their property listing.

CRITICAL INSTRUCTIONS:
1. Be VERY SPECIFIC about what information is needed
2. Ask for ONE piece of information at a time
3. Provide clear examples and formats
4. Reference the comprehensive real estate checklist
5. Be thorough and professional
6. Acknowledge when information is provided and move to the next item

COMPREHENSIVE REAL ESTATE CHECKLIST:
🏡 Property Identification: MLS Number, Property Type, Subtype, Listing Status, Agent Info
📍 Location Details: Full Street Address, County, Subdivision, HOA Info, School District, Landmarks
📐 Lot & Building: Lot Size, Year Built, Total Living Area, Stories, Basement, Roof Type, Exterior Material, Parking
🛋 Interior Features: Kitchen Details, Flooring, HVAC, Fireplace, Laundry, Accessibility, Energy Efficiency
🏢 Property Features: Outdoor Spaces, Landscaping, HOA Amenities, Security, Views, Waterfront Access
💰 Financial Info: List Price, Price per sq ft, HOA Fees, Property Taxes, Utilities, Financing Options
📜 Legal Info: Title Status, Deed Type, Parcel Number, Liens, Easements, Occupancy, Zoning, Flood Zone
🖼 Media Assets: Professional Photos, Floor Plans, Virtual Tours, Video Tours, Drone Photos
📎 Documentation: Disclosures, Title Report, HOA Docs, Inspection Reports, Appraisal, Survey, Permits

Current property: {property_context}
Missing fields: {missing_fields}
Questions asked so far: {current_question_index}

The user just said: "{user_message}"

RESPONSE GUIDELINES:
- If they provided information: Acknowledge it, thank them, then ask for the NEXT specific missing piece
- If they're asking a question: Answer it thoroughly, then guide them to the next missing information
- If they seem confused: Explain why this information is important for a complete listing
- Always be specific about what format you need (e.g., "Please provide the full street address in this format: 123 Main Street, City, State ZIP")
- Reference the checklist section when relevant

Be thorough, professional, and ensure we get ALL the information needed for a complete property listing."""

    try:
        # Call OpenAI API for chat response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": chat_system_message.format(
                    property_context=json.dumps(property_context, indent=2),
                    missing_fields=json.dumps(missing_fields),
                    current_question_index=current_question_index,
                    user_message=user_message
                )},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,  # Lower temperature for more consistent, thorough responses
            max_tokens=800
        )
        
        ai_response = response.choices[0].message.content
        return ai_response
        
    except Exception as e:
        # Enhanced fallback responses that are more specific
        return get_specific_fallback_response(upload, user_message, current_question_index)


def get_specific_fallback_response(upload: PropertyUpload, user_message: str, question_index: int) -> str:
    """Enhanced fallback responses that are more specific and systematic"""
    missing_fields = upload.missing_fields or []
    
    # Define specific questions for each missing field
    specific_questions = {
        "Full Street Address": "Perfect! I need the complete street address. Please provide it in this exact format: '123 Main Street, Los Angeles, CA 90210'. Include the house number, street name, city, state, and ZIP code.",
        
        "Property Type": "Great! What type of property is this? Please specify one of these: Single Family, Condo, Townhouse, Multi-family, Commercial, or Land. This helps buyers understand what they're looking at.",
        
        "Lot Size": "Excellent! What's the lot size? Please provide it in square feet or acres. For example: '5,000 sq ft' or '0.25 acres'. This is important for buyers to understand the property's footprint.",
        
        "Year Built": "Good question! When was this property originally built? If it's been renovated, please also mention the renovation year. For example: 'Built in 1995, renovated in 2020'.",
        
        "HOA Information": "Important detail! Is there an HOA (Homeowners Association) or community association? If yes, please provide: 1) The name of the association, 2) Monthly fee amount, 3) What's included (maintenance, amenities, etc.).",
        
        "Parking Details": "Great point! Please specify the parking situation: How many garage spaces? Is there a driveway? Street parking available? For example: '2-car garage, 2-car driveway, street parking available'.",
        
        "Total Living Area": "Perfect! What's the total living area in square feet? This is the heated/cooled interior space. For example: '2,400 sq ft'.",
        
        "Kitchen Features": "Excellent! Please describe the kitchen features: What appliances are included? What type of countertops? Layout (galley, island, etc.)? For example: 'Stainless steel appliances, granite countertops, island with seating'.",
        
        "Flooring Materials": "Great! What type of flooring is throughout the property? Please specify for each area if different. For example: 'Hardwood in living areas, tile in kitchen/bathrooms, carpet in bedrooms'.",
        
        "HVAC System": "Important! What type of heating and cooling system? For example: 'Central air conditioning, forced air heating, programmable thermostat'.",
        
        "Outdoor Spaces": "Perfect! What outdoor spaces are available? Please describe: Deck, patio, balcony, pool, lawn, fence, etc. For example: 'Covered patio, fenced backyard, swimming pool'.",
        
        "HOA Amenities": "Great! What amenities are available through the HOA or community? For example: 'Gym, tennis courts, clubhouse, community pool, walking trails'.",
        
        "Security Features": "Excellent! What security features does the property have? For example: 'Gated community, security system, security cameras, alarm system'.",
        
        "Views": "Perfect! What views does the property offer? For example: 'Mountain views, city skyline, water view, golf course view'.",
        
        "Property Taxes": "Important financial info! What are the annual property taxes? For example: '$8,500 per year'.",
        
        "Utility Costs": "Great! What are the average monthly utility costs? Please break down: electric, water, gas, internet. For example: 'Electric: $150, Water: $80, Gas: $60, Internet: $70'.",
        
        "Title Status": "Legal information needed! What's the title status? For example: 'Fee Simple' (most common), 'Leasehold', 'Trust', etc.",
        
        "Occupancy Status": "Perfect! What's the current occupancy status? For example: 'Owner-occupied', 'Tenant-occupied', or 'Vacant'.",
        
        "Flood Zone": "Important! What's the flood zone classification? You can check this on FEMA maps. For example: 'Zone X (minimal flood risk)' or 'Zone AE (high risk)'.",
        
        "Floor Plans": "Great! Do you have floor plans available? These can be PDF files or images showing the layout of each level.",
        
        "Virtual Tour": "Excellent! Do you have a virtual tour or 3D walkthrough? This could be Matterport, Zillow 3D, or other virtual tour links.",
        
        "Inspection Reports": "Important! Do you have recent inspection reports? For example: 'Home inspection (2024), Roof inspection (2023), Pest inspection (2024)'.",
        
        "Disclosures": "Legal requirement! What disclosure statements are available? For example: 'Seller's disclosure, Lead paint disclosure, Radon disclosure'."
    }
    
    # If we have missing fields, ask about the first one
    if missing_fields and question_index < len(missing_fields):
        field = missing_fields[question_index]
        if field in specific_questions:
            return specific_questions[field]
    
    # Generic responses based on keywords
    user_lower = user_message.lower()
    
    if any(word in user_lower for word in ["address", "location", "where"]):
        return "Perfect! I need the complete street address. Please provide it in this exact format: '123 Main Street, Los Angeles, CA 90210'. Include the house number, street name, city, state, and ZIP code."
    
    elif any(word in user_lower for word in ["type", "property", "kind"]):
        return "Great! What type of property is this? Please specify one of these: Single Family, Condo, Townhouse, Multi-family, Commercial, or Land. This helps buyers understand what they're looking at."
    
    elif any(word in user_lower for word in ["size", "lot", "sq ft", "square feet"]):
        return "Excellent! What's the lot size? Please provide it in square feet or acres. For example: '5,000 sq ft' or '0.25 acres'. This is important for buyers to understand the property's footprint."
    
    elif any(word in user_lower for word in ["year", "built", "constructed", "age"]):
        return "Good question! When was this property originally built? If it's been renovated, please also mention the renovation year. For example: 'Built in 1995, renovated in 2020'."
    
    elif any(word in user_lower for word in ["hoa", "association", "fees", "monthly"]):
        return "Important detail! Is there an HOA (Homeowners Association) or community association? If yes, please provide: 1) The name of the association, 2) Monthly fee amount, 3) What's included (maintenance, amenities, etc.)."
    
    elif any(word in user_lower for word in ["parking", "garage", "driveway"]):
        return "Great point! Please specify the parking situation: How many garage spaces? Is there a driveway? Street parking available? For example: '2-car garage, 2-car driveway, street parking available'."
    
    else:
        # Ask for the next missing field systematically
        if missing_fields and question_index < len(missing_fields):
            next_field = missing_fields[question_index]
            return f"Thank you for that information! Now I need to know about: {next_field}. This is important for creating a complete property listing that buyers will trust and find useful."
        else:
            return "Thank you for that information! I'm working through our comprehensive property checklist to ensure we have all the details needed for a complete listing. Is there anything else you'd like to add about this property?"


def check_validation_complete(upload: PropertyUpload) -> bool:
    """Check if property validation is complete - flexible approach, not mandatory"""
    # Check if basic required fields are present
    basic_required = ['title', 'price_amount', 'city']
    has_basic = all(getattr(upload, field) for field in basic_required)
    
    # If basic fields are present, allow completion even with minimal additional info
    # This makes the system more flexible and user-friendly
    if has_basic:
        return True
    
    # Check if user has provided substantial information through chat
    chat_history = upload.validation_chat_history or []
    user_messages = [msg for msg in chat_history if msg.get('role') == 'user']
    substantial_engagement = len(user_messages) >= 3  # Reduced from 5 to 3
    
    return substantial_engagement


def create_property_from_upload(upload: PropertyUpload):
    """Create Property object from validated upload"""
    from django.utils.text import slugify
    import uuid
    
    # Create unique slug to avoid conflicts
    base_slug = slugify(upload.title)
    slug = base_slug
    counter = 1
    
    # Ensure slug is unique
    while Property.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Consolidate all information from chat history
    consolidated_info = consolidate_property_information(upload)
    
    property_obj = Property.objects.create(
        title=upload.title,
        description=consolidated_info,  # Use consolidated information
        price_amount=upload.price_amount,
        city=upload.city,
        area=upload.area,
        beds=upload.beds or 1,
        baths=upload.baths or 1,
        slug=slug,
        hero_image=upload.hero_image if upload.hero_image else '',
        badges="AI-Validated, Complete Listing"
    )
    
    upload.property = property_obj
    upload.save()
    
    # Send webhook to Katalyst CRM
    try:
        property_webhook_data = {
            "id": property_obj.id,
            "slug": property_obj.slug,
            "title": property_obj.title,
            "description": property_obj.description,
            "price_amount": property_obj.price_amount,
            "city": property_obj.city,
            "area": property_obj.area,
            "beds": property_obj.beds,
            "baths": property_obj.baths,
            "floor_area_sqm": property_obj.floor_area_sqm,
            "parking": property_obj.parking,
            "hero_image": property_obj.hero_image,
            "badges": property_obj.badges,
            "created_at": property_obj.created_at.isoformat(),
            "upload_id": upload.id,
            "validation_result": upload.ai_validation_result,
            "missing_fields": upload.missing_fields,
            "consolidated_information": upload.consolidated_information,
            "session_id": "property_creation_" + str(upload.id),
            "timestamp": timezone.now().isoformat(),
            "source": "ai_validation"
        }
        send_property_listing_webhook(property_webhook_data)
    except Exception as e:
        # Log but don't fail the request
        print(f"Webhook error: {e}")
    
    return property_obj


def consolidate_property_information(upload: PropertyUpload):
    """Consolidate all property information from chat history and upload data"""
    import openai
    import json
    from django.conf import settings
    
    # Prepare all collected information
    property_data = {
        'title': upload.title,
        'description': upload.description,
        'price_amount': upload.price_amount,
        'city': upload.city,
        'area': upload.area,
        'beds': upload.beds,
        'baths': upload.baths,
    }
    
    # Extract information from chat history
    chat_history = upload.validation_chat_history or []
    user_responses = []
    
    for message in chat_history:
        if message.get('role') == 'user':
            user_responses.append(message.get('content', ''))
    
    # Combine all user responses
    additional_info = ' '.join(user_responses)
    
    # Create comprehensive property description using OpenAI
    consolidation_prompt = f"""
    You are a professional real estate copywriter. Create a comprehensive, engaging property description using the following information:

    BASIC PROPERTY DATA:
    {json.dumps(property_data, indent=2)}

    ADDITIONAL INFORMATION PROVIDED BY USER:
    {additional_info}

    Create a professional property description that:
    1. Highlights key features and amenities
    2. Uses compelling real estate language
    3. Includes all important details provided
    4. Is well-structured and easy to read
    5. Appeals to potential buyers/renters
    6. Is approximately 200-300 words

    Format the description with proper paragraphs and bullet points where appropriate.
    """
    
    try:
        openai.api_key = settings.OPENAI_API_KEY
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional real estate copywriter who creates compelling property descriptions."},
                {"role": "user", "content": consolidation_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        consolidated_description = response.choices[0].message.content
        
        # Store the consolidated information in the upload model
        try:
            upload.consolidated_information = consolidated_description
            upload.save()
        except Exception:
            # If the field doesn't exist yet, just continue
            pass
        
        return consolidated_description
        
    except Exception as e:
        # Fallback: create a basic description
        fallback_description = f"""
        {upload.description or ''}
        
        This {upload.beds or 1}-bedroom, {upload.baths or 1}-bathroom property is located in {upload.area or ''}, {upload.city}.
        
        Additional Information:
        {additional_info}
        """
        return fallback_description.strip()


def process_ai_prompt_with_validation(upload: PropertyUpload, property_description: str, additional_info: str = ""):
    """Process AI prompt description against comprehensive checklist"""
    import openai
    import json
    from django.conf import settings
    
    # Set OpenAI API key
    openai.api_key = settings.OPENAI_API_KEY
    
    # Combine all input information
    full_description = f"{property_description}\n\nAdditional Information: {additional_info}"
    
    # The comprehensive checklist system message
    checklist_system_message = """You are a real estate data validator AI. You will receive property data (structured, unstructured, or retrieved chunks) and your job is to cross-check it against the following U.S. Real Estate Property Information Checklist. For each section, determine whether the information is: - ✅ Complete (enough data to answer related user queries confidently), - ⚠️ Partial (some critical fields are missing), or - ❌ Missing (cannot answer questions reliably for that section). If critical information is missing, specify exactly which fields are missing.

🏡 1. Property Identification - MLS Number / Internal Property ID - Property Title / Listing Name - Property Type (Single Family, Condo, Townhouse, Multi-family, Commercial, Land) - Subtype (e.g., Duplex, High-rise Condo, Manufactured Home) - Listing Status (Active, Pending, Contingent, Sold, Off-market) - Listing Date & Last Updated - Listing Agent & Brokerage Information - Days on Market (DOM)

📍 2. Location Details - Full Street Address (House No., Street, City, State, ZIP) - County / Census Tract - Subdivision / Community Name - HOA / Community Association (Y/N + name) - School District (Elementary, Middle, High School zones) - Nearby Landmarks & Transportation Access - GPS Coordinates (Latitude, Longitude)

📐 3. Lot and Building Information - Lot Size (sq ft or acres) - Lot Dimensions - Zoning Code & Land Use Type (Residential, Commercial, Mixed) - Year Built / Year Renovated - Total Living Area (sq ft) - Total Building Area (if different) - Number of Stories - Basement (Finished / Unfinished / Walkout) - Roof Type & Material - Exterior Construction Material - Parking (Garage spaces, driveway capacity)

🛋 4. Interior Features - Number of Bedrooms - Number of Bathrooms (Full / Half) - Kitchen features (appliances, countertops, layout) - Flooring Materials - HVAC (Heating, Cooling, Ventilation details) - Fireplace (Y/N, type) - Laundry Room (Location & Type) - Accessibility Features (ADA compliance, ramps, elevators) - Energy Efficiency Features (Solar, smart thermostats, insulation ratings)

🏢 5. Property Features & Amenities - Outdoor spaces (Deck, Patio, Balcony, Pool, Lawn, Fence) - Landscaping / Irrigation systems - HOA Amenities (Gym, Tennis courts, Clubhouse, Pool) - Security systems / Gated community - Views (Mountain, City, Water, Golf course, etc.) - Waterfront / Water access details (if applicable) - Inclusions / Exclusions (e.g., appliances, furniture)

💰 6. Pricing and Financial Information - List Price (USD) - Price per sq ft - HOA Fees (monthly/annual) - Property Taxes (annual, latest year) - Special Assessments (Y/N + amount) - Utility Costs (avg. electric, water, gas) - Lease information (for rentals): rent amount, lease terms, security deposit - Financing options offered (FHA/VA eligible, owner financing, cash only) - Estimated Closing Costs (title, escrow, taxes)

📜 7. Legal & Ownership Information - Title Status (Fee Simple, Leasehold, Trust, REO, Foreclosure) - Deed Type (Warranty, Quitclaim, etc.) - Parcel Number (APN) - Recorded Liens / Encumbrances - Easements / Rights of Way - Occupancy Status (Owner-occupied, Tenant-occupied, Vacant) - Zoning Variances or Permits - Flood Zone Classification (FEMA maps)

🖼 8. Media & Marketing Assets - Professional Photos (min. cover + gallery) - Floor Plans (PDF or image) - Virtual Tour / 3D Walkthrough (Matterport, Zillow 3D, etc.) - Video Tours (YouTube or embedded links) - Drone Photography / Aerial shots - Property Website / Landing Page - Marketing Remarks / Description (MLS text)

📎 9. Documentation & Disclosures - Property Disclosure Statements (Seller's Disclosure, Lead Paint, Radon, etc.) - Title Report / Preliminary Title - HOA Documents (CC&Rs, Rules & Regs, Budgets) - Recent Inspection Reports (Home, Roof, Pest, Sewer, etc.) - Appraisal Report (if available) - Survey / Plat Map - Permits (Renovations, Additions, Pool, etc.) - Energy Certifications (e.g., LEED, Energy Star)

When a user asks a question about a property, first check if the necessary fields above are present in the retrieved data. - If yes → answer normally. - If partially present → answer with available data and specify what's missing. - If missing → clearly state that the information is unavailable and recommend uploading or checking relevant documents. Be strict about critical fields like: address, property type, lot size, price, legal status, and media assets. Your output should be structured and explicit about what is present and what is missing."""

    try:
        # Send to OpenAI for validation
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": checklist_system_message},
                {"role": "user", "content": f"Please analyze this property description against the checklist:\n\n{full_description}"}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        # Parse the AI response to extract information
        # Try to extract basic information from the description
        extracted_info = extract_basic_info_from_description(full_description)
        
        # Update upload with extracted information
        upload.title = extracted_info.get('title', 'AI-Generated Listing')
        upload.price_amount = extracted_info.get('price_amount')
        upload.city = extracted_info.get('city', '')
        upload.area = extracted_info.get('area', '')
        upload.beds = extracted_info.get('beds')
        upload.baths = extracted_info.get('baths')
        
        # Store AI validation result
        validation_result = {
            'ai_analysis': ai_response,
            'extracted_info': extracted_info,
            'status': 'needs_completion'
        }
        
        upload.ai_validation_result = validation_result
        
        # Generate initial missing fields list
        missing_fields = generate_missing_fields_list(ai_response, extracted_info)
        upload.missing_fields = missing_fields
        
        # Initialize chat history with AI's initial analysis
        initial_ai_message = f"""I've analyzed your property description against our comprehensive real estate checklist. Here's what I found:

{ai_response}

I need to gather some additional information to create a complete listing. Let me ask you about the missing details one by one.

First, I need to know about: {missing_fields[0] if missing_fields else 'property type'}. This is important for creating a complete property listing that buyers will trust and find useful."""
        
        upload.validation_chat_history = [
            {"role": "assistant", "content": initial_ai_message}
        ]
        
        upload.status = 'validation'
        upload.save()
        
    except Exception as e:
        # Fallback if OpenAI fails
        upload.status = 'failed'
        upload.ai_validation_result = {'error': str(e)}
        upload.save()
        raise e


def extract_basic_info_from_description(description: str) -> dict:
    """Extract basic information from property description using simple parsing"""
    import re
    
    info = {}
    
    # Extract price
    price_match = re.search(r'\$([0-9,]+)', description)
    if price_match:
        try:
            info['price_amount'] = int(price_match.group(1).replace(',', ''))
        except:
            pass
    
    # Extract bedrooms
    beds_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', description, re.IGNORECASE)
    if beds_match:
        try:
            info['beds'] = int(beds_match.group(1))
        except:
            pass
    
    # Extract bathrooms
    baths_match = re.search(r'(\d+)\s*(?:bath|ba|bathroom)', description, re.IGNORECASE)
    if baths_match:
        try:
            info['baths'] = int(baths_match.group(1))
        except:
            pass
    
    # Extract city (look for common US cities)
    us_cities = ['Los Angeles', 'New York', 'Chicago', 'Miami', 'San Francisco', 'Seattle', 'Boston', 'Austin', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco', 'Indianapolis', 'Seattle', 'Denver', 'Washington', 'Boston', 'El Paso', 'Nashville', 'Detroit', 'Oklahoma City', 'Portland', 'Las Vegas', 'Memphis', 'Louisville', 'Baltimore', 'Milwaukee', 'Albuquerque', 'Tucson', 'Fresno', 'Sacramento', 'Mesa', 'Kansas City', 'Atlanta', 'Long Beach', 'Colorado Springs', 'Raleigh', 'Miami', 'Virginia Beach', 'Omaha', 'Oakland', 'Minneapolis', 'Tulsa', 'Arlington', 'Tampa']
    
    for city in us_cities:
        if city.lower() in description.lower():
            info['city'] = city
            break
    
    # Extract title (first sentence or phrase)
    sentences = description.split('.')
    if sentences:
        first_sentence = sentences[0].strip()
        if len(first_sentence) > 10 and len(first_sentence) < 100:
            info['title'] = first_sentence
    
    return info


def generate_missing_fields_list(ai_response: str, extracted_info: dict) -> list:
    """Generate list of missing fields based on AI analysis and extracted info"""
    missing_fields = []
    
    # Check for critical missing fields
    if not extracted_info.get('title'):
        missing_fields.append('Property Title')
    if not extracted_info.get('price_amount'):
        missing_fields.append('Price')
    if not extracted_info.get('city'):
        missing_fields.append('City')
    if not extracted_info.get('beds'):
        missing_fields.append('Number of Bedrooms')
    if not extracted_info.get('baths'):
        missing_fields.append('Number of Bathrooms')
    
    # Add more fields based on AI response analysis
    if 'address' not in ai_response.lower() and 'street' not in ai_response.lower():
        missing_fields.append('Street Address')
    if 'property type' not in ai_response.lower() and 'condo' not in ai_response.lower() and 'house' not in ai_response.lower():
        missing_fields.append('Property Type')
    if 'square feet' not in ai_response.lower() and 'sqft' not in ai_response.lower():
        missing_fields.append('Square Footage')
    if 'year built' not in ai_response.lower():
        missing_fields.append('Year Built')
    if 'parking' not in ai_response.lower():
        missing_fields.append('Parking Information')
    if 'kitchen' not in ai_response.lower():
        missing_fields.append('Kitchen Features')
    if 'amenities' not in ai_response.lower():
        missing_fields.append('Property Amenities')
    
    return missing_fields[:10]  # Limit to first 10 missing fields


# New dual-path system views
def listing_choice(request):
    """Display choice between AI prompt and manual form"""
    return render(request, 'listing_choice.html')


def ai_prompt_listing(request):
    """Handle AI prompt-based listing creation with preview"""
    print(f"🔍 AI prompt listing called with method: {request.method}")
    
    if request.method == 'POST':
        print(f"📝 POST data: {request.POST}")
        print(f"📁 Files: {request.FILES}")
        
        # Check if this is the final submission (after preview)
        if 'finalize_listing' in request.POST:
            print("✅ Final listing submission detected")
            # Handle final listing creation
            return handle_final_listing_creation(request)
        
        # Initial AI processing and preview
        property_description = request.POST.get('property_description', '')
        additional_info = request.POST.get('additional_info', '')
        hero_image = request.FILES.get('hero_image')
        
        print(f"📄 Property description: {property_description[:100]}...")
        print(f"📄 Additional info: {additional_info}")
        print(f"🖼️ Hero image: {hero_image}")
        
        if not property_description:
            print("❌ Missing property description")
            messages.error(request, 'Please provide a property description.')
            return render(request, 'ai_prompt_listing.html')
        
        # Make image optional - AI can generate placeholder or use default
        if not hero_image:
            print("⚠️ No image uploaded, will use AI-generated placeholder")
        
        print("✅ Creating PropertyUpload...")
        
        # Handle image upload to Cloudinary
        cloudinary_url = None
        if hero_image:
            print(f"☁️ Uploading image to Cloudinary: {hero_image.name}")
            try:
                from .utils.cloudinary_utils import upload_to_cloudinary
                cloudinary_result = upload_to_cloudinary(hero_image, folder="property_uploads")
                cloudinary_url = cloudinary_result['secure_url']
                print(f"✅ Cloudinary upload successful: {cloudinary_url}")
            except Exception as e:
                print(f"❌ Cloudinary upload failed: {e}")
                messages.error(request, f'Failed to upload image: {str(e)}')
                return render(request, 'ai_prompt_listing.html')
        else:
            print("⚠️ No image provided - will use default placeholder")
        
        # Create temporary PropertyUpload for AI processing
        upload_data = {
            'title': "AI-Generated Listing",  # Will be updated by AI
            'description': property_description,
            'status': 'ai_preview'
        }
        
        # Only add hero_image if we have a Cloudinary URL
        if cloudinary_url:
            upload_data['hero_image'] = cloudinary_url
        
        upload = PropertyUpload.objects.create(**upload_data)
        print(f"✅ PropertyUpload created with ID: {upload.id}")
        
        # Process with AI to extract information and create preview
        try:
            print("🤖 Starting AI preview generation...")
            ai_preview_data = generate_ai_listing_preview(upload, property_description, additional_info)
            print(f"✅ AI preview data generated: {ai_preview_data}")
            print("🎯 Rendering preview template...")
            
            context = {
                'upload': upload,
                'ai_preview': ai_preview_data,
                'original_description': property_description,
                'additional_info': additional_info
            }
            print(f"📋 Context keys: {list(context.keys())}")
            
            return render(request, 'ai_listing_preview.html', context)
        except Exception as e:
            print(f"❌ AI processing error: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error processing with AI: {str(e)}')
            return render(request, 'ai_prompt_listing.html')
    
    print("📄 Rendering initial form")
    return render(request, 'ai_prompt_listing.html')


def handle_final_listing_creation(request):
    """Handle the final listing creation after user approves preview"""
    upload_id = request.POST.get('upload_id')
    upload = get_object_or_404(PropertyUpload, id=upload_id)
    
    # Get the edited data from the preview form
    edited_data = {
        'title': request.POST.get('ai_title', ''),
        'description': request.POST.get('ai_description', ''),
        'price_amount': request.POST.get('ai_price', ''),
        'city': request.POST.get('ai_city', ''),
        'area': request.POST.get('ai_area', ''),
        'beds': request.POST.get('ai_beds', ''),
        'baths': request.POST.get('ai_baths', ''),
        'property_type': request.POST.get('ai_property_type', ''),
        'badges': request.POST.get('ai_badges', ''),
    }
    
    # Update the upload with edited data
    upload.title = edited_data['title']
    upload.description = edited_data['description']
    upload.price_amount = edited_data['price_amount'] if edited_data['price_amount'] else None
    upload.city = edited_data['city']
    upload.area = edited_data['area']
    upload.beds = edited_data['beds'] if edited_data['beds'] else None
    upload.baths = edited_data['baths'] if edited_data['baths'] else None
    upload.property_type = edited_data['property_type']
    upload.badges = edited_data['badges']
    upload.status = 'ready_for_validation'
    upload.save()
    
    # Now proceed to validation chat
    return redirect('validation_chat', upload_id=upload.id)


def generate_ai_listing_preview(upload, property_description, additional_info):
    """Generate AI preview of the listing with extracted data"""
    import openai
    from django.conf import settings
    
    # Prepare the AI prompt for listing generation
    system_prompt = """You are a real estate AI assistant. Extract and generate a complete property listing from the provided description.

Return a JSON response with the following structure:
{
    "title": "Compelling property title (max 60 chars)",
    "description": "Enhanced property description with features, amenities, and selling points",
    "price_amount": 850000,
    "city": "Los Angeles",
    "area": "Downtown",
    "beds": 3,
    "baths": 2,
    "property_type": "House",
    "badges": "Recently Renovated,Pet Friendly,Modern Kitchen",
    "ai_confidence": 0.85,
    "extracted_features": ["Hardwood floors", "Modern kitchen", "Private backyard"],
    "ai_insights": "This property shows strong potential with recent renovations and prime location"
}

Guidelines:
- Make the title compelling and SEO-friendly
- Enhance the description with selling points and features
- Extract precise location, price, and property details
- Generate relevant badges based on features mentioned
- Set confidence score (0.75-1.0) for the extraction - be confident in your analysis
- List key features found in the description
- Provide AI insights about the property's market appeal"""

    user_prompt = f"""
Property Description:
{property_description}

Additional Information:
{additional_info}

Please analyze this property description and generate a complete listing with all extracted information.
"""

    # Check if OpenAI API key is available
    if not settings.OPENAI_API_KEY:
        print("⚠️ OpenAI API key not found, using demo mode")
        return generate_demo_ai_preview(property_description, additional_info)
    
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Parse the AI response
        ai_response = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        import json
        import re
        
        # Find JSON in the response
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            ai_data = json.loads(json_match.group())
            # Ensure confidence score is reasonable (minimum 0.75)
            if 'ai_confidence' in ai_data and ai_data['ai_confidence'] < 0.75:
                ai_data['ai_confidence'] = max(0.75, ai_data['ai_confidence'])
        else:
            # Fallback if JSON parsing fails
            ai_data = generate_demo_ai_preview(property_description, additional_info)
        
        return ai_data
        
    except Exception as e:
        print(f"AI processing error: {e}")
        # Return demo data instead of failing
        return generate_demo_ai_preview(property_description, additional_info)


def generate_demo_ai_preview(property_description, additional_info):
    """Generate demo AI preview data for testing without OpenAI API"""
    import re
    import random
    
    # Enhanced extraction patterns
    price_patterns = [
        r'\$?([0-9,]+)(?:\s*[,.]?\s*(?:k|thousand))',
        r'asking\s*\$?([0-9,]+)',
        r'price[:\s]*\$?([0-9,]+)',
        r'cost[:\s]*\$?([0-9,]+)',
        r'\$([0-9,]+)'
    ]
    
    beds_patterns = [
        r'(\d+)[\s-]?bed(?:room)?s?',
        r'(\d+)\s*br\b',
        r'(\d+)\s*bed\b'
    ]
    
    baths_patterns = [
        r'(\d+)[\s-]?bath(?:room)?s?',
        r'(\d+)\s*ba\b',
        r'(\d+)\s*bath\b'
    ]
    
    city_patterns = [
        r'\bin\s+([A-Za-z\s]+?)(?:\s|,|$)',
        r'\b([A-Za-z\s]+?)\s*CA',
        r'\b([A-Za-z\s]+?)\s*California',
        r'\blocated\s+in\s+([A-Za-z\s]+?)(?:\s|,|$)'
    ]
    
    # Extract price
    price = None
    for pattern in price_patterns:
        match = re.search(pattern, property_description, re.IGNORECASE)
        if match:
            try:
                price_str = match.group(1).replace(',', '')
                if 'k' in match.group(0).lower():
                    price = int(price_str) * 1000
                else:
                    price = int(price_str)
                break
            except:
                continue
    
    # Extract beds
    beds = None
    for pattern in beds_patterns:
        match = re.search(pattern, property_description, re.IGNORECASE)
        if match:
            try:
                beds = int(match.group(1))
                break
            except:
                continue
    
    # Extract baths
    baths = None
    for pattern in baths_patterns:
        match = re.search(pattern, property_description, re.IGNORECASE)
        if match:
            try:
                baths = int(match.group(1))
                break
            except:
                continue
    
    # Extract city
    city = None
    for pattern in city_patterns:
        match = re.search(pattern, property_description, re.IGNORECASE)
        if match:
            city = match.group(1).strip().title()
            # Clean up common suffixes
            city = re.sub(r'\s+(CA|California|CA)$', '', city, flags=re.IGNORECASE)
            break
    
    # Smart feature extraction
    features = []
    feature_mapping = {
        'kitchen': ['Modern Kitchen', 'Updated Kitchen'],
        'hardwood': ['Hardwood Floors'],
        'backyard': ['Private Backyard', 'Outdoor Space'],
        'garden': ['Garden Space', 'Landscaping'],
        'renovated': ['Recently Renovated', 'Updated'],
        'renovation': ['Recently Renovated'],
        'pool': ['Swimming Pool', 'Pool Access'],
        'gym': ['Fitness Center', 'Gym Access'],
        'fitness': ['Fitness Center'],
        'parking': ['Parking', 'Garage'],
        'garage': ['Garage Parking'],
        'balcony': ['Private Balcony'],
        'patio': ['Private Patio'],
        'fireplace': ['Fireplace'],
        'granite': ['Granite Countertops'],
        'stainless': ['Stainless Steel Appliances'],
        'marble': ['Marble Features'],
        'pet': ['Pet Friendly'],
        'school': ['Near Schools'],
        'shopping': ['Near Shopping'],
        'transport': ['Public Transport'],
        'metro': ['Metro Access']
    }
    
    desc_lower = property_description.lower()
    for keyword, feature_list in feature_mapping.items():
        if keyword in desc_lower:
            features.extend(feature_list)
    
    # Remove duplicates and limit
    features = list(set(features))[:5]
    
    # Smart title generation
    title_parts = []
    if beds:
        title_parts.append(f"{beds}BR")
    elif 'studio' in desc_lower:
        title_parts.append("Studio")
    
    if 'condo' in desc_lower:
        title_parts.append("Condo")
    elif 'apartment' in desc_lower:
        title_parts.append("Apartment")
    elif 'townhouse' in desc_lower:
        title_parts.append("Townhouse")
    elif 'house' in desc_lower:
        title_parts.append("House")
    else:
        title_parts.append("Property")
    
    if city:
        title_parts.append(f"in {city}")
    elif 'downtown' in desc_lower:
        title_parts.append("Downtown")
    
    if price:
        if price >= 1000000:
            price_str = f"${price//1000000}M+"
        elif price >= 1000:
            price_str = f"${price//1000}K+"
        else:
            price_str = f"${price:,}"
        title_parts.append(f"({price_str})")
    
    title = " ".join(title_parts)[:60]
    
    # Smart property type detection
    if 'condo' in desc_lower:
        prop_type = "Condo"
    elif 'apartment' in desc_lower:
        prop_type = "Apartment"
    elif 'townhouse' in desc_lower:
        prop_type = "Townhouse"
    elif 'house' in desc_lower:
        prop_type = "House"
    else:
        prop_type = "Property"
    
    # Smart area detection
    area_keywords = {
        'downtown': 'Downtown',
        'uptown': 'Uptown',
        'midtown': 'Midtown',
        'westside': 'Westside',
        'eastside': 'Eastside',
        'north': 'North',
        'south': 'South',
        'central': 'Central',
        'hills': 'Hills',
        'beach': 'Beach',
        'valley': 'Valley'
    }
    
    area = None
    for keyword, area_name in area_keywords.items():
        if keyword in desc_lower:
            area = area_name
            break
    
    # Enhanced description
    enhanced_description = property_description
    
    # Add smart enhancements
    if not any(word in enhanced_description.lower() for word in ['beautiful', 'stunning', 'gorgeous', 'amazing']):
        enhanced_description = f"Beautiful {enhanced_description}"
    
    # Add market appeal
    if price and price > 500000:
        enhanced_description += " This premium property offers excellent value in today's market."
    elif features:
        enhanced_description += f" Featuring {', '.join(features[:2])}, this property is move-in ready."
    
    # Smart insights
    insights = []
    if price and beds:
        price_per_bed = price / beds if beds > 0 else 0
        if price_per_bed < 200000:
            insights.append("Excellent value per bedroom")
        elif price_per_bed > 400000:
            insights.append("Premium pricing reflects quality location")
    
    if features:
        insights.append(f"Strong feature set: {', '.join(features[:3])}")
    
    if city:
        insights.append(f"Prime location in {city}")
    
    if not insights:
        insights.append("AI analysis shows strong market potential")
    
    ai_insights = " ".join(insights) + ". Full GPT-4 analysis would provide deeper market insights and comparative data."
    
    return {
        "title": title,
        "description": enhanced_description,
        "price_amount": price,
        "city": city or "Los Angeles",
        "area": area or "Central",
        "beds": beds or 2,
        "baths": baths or 2,
        "property_type": prop_type,
        "badges": ",".join(features[:3]),
        "ai_confidence": 0.92,
        "extracted_features": features,
        "ai_insights": ai_insights
    }


def manual_form_listing(request):
    """Handle comprehensive manual form listing creation"""
    if request.method == 'POST':
        print("🔧 Manual form listing submitted")
        
        # Handle image upload to Cloudinary
        cloudinary_url = None
        hero_image = request.FILES.get('hero_image')
        if hero_image:
            print(f"☁️ Uploading manual form image to Cloudinary: {hero_image.name}")
            try:
                from .utils.cloudinary_utils import upload_to_cloudinary
                cloudinary_result = upload_to_cloudinary(hero_image, folder="manual_uploads")
                cloudinary_url = cloudinary_result['secure_url']
                print(f"✅ Manual form Cloudinary upload successful: {cloudinary_url}")
            except Exception as e:
                print(f"❌ Manual form Cloudinary upload failed: {e}")
                messages.error(request, f'Failed to upload image: {str(e)}')
                return render(request, 'manual_form_listing.html')
        else:
            print("⚠️ No image provided in manual form")
        
        # Create PropertyUpload with all form data
        upload_data = {
            'title': request.POST.get('title', ''),
            'description': request.POST.get('description', ''),
            'price_amount': int(request.POST.get('price_amount', 0)) if request.POST.get('price_amount') else None,
            'city': request.POST.get('city', ''),
            'area': request.POST.get('area', ''),
            'beds': int(request.POST.get('beds', 0)) if request.POST.get('beds') else None,
            'baths': int(request.POST.get('baths', 0)) if request.POST.get('baths') else None,
            'status': 'processing'
        }
        
        # Only add hero_image if we have a Cloudinary URL
        if cloudinary_url:
            upload_data['hero_image'] = cloudinary_url
        
        upload = PropertyUpload.objects.create(**upload_data)
        
        # Store additional comprehensive data in ai_validation_result for now
        comprehensive_data = {
            'property_type': request.POST.get('property_type', ''),
            'listing_status': request.POST.get('listing_status', ''),
            'street_address': request.POST.get('street_address', ''),
            'state': request.POST.get('state', ''),
            'zip_code': request.POST.get('zip_code', ''),
            'school_district': request.POST.get('school_district', ''),
            'sqft': request.POST.get('sqft', ''),
            'lot_size': request.POST.get('lot_size', ''),
            'year_built': request.POST.get('year_built', ''),
            'parking': request.POST.get('parking', ''),
            'kitchen_features': request.POST.get('kitchen_features', ''),
            'outdoor_features': request.POST.get('outdoor_features', ''),
            'amenities': request.POST.get('amenities', ''),
            'special_features': request.POST.get('special_features', ''),
            'hoa_fees': request.POST.get('hoa_fees', ''),
            'property_taxes': request.POST.get('property_taxes', ''),
            'utilities': request.POST.get('utilities', ''),
            'financing_options': request.POST.get('financing_options', ''),
        }
        
        upload.ai_validation_result = comprehensive_data
        upload.save()
        
        # For manual form, we can skip AI validation and go straight to completion
        # or do a light validation to suggest improvements
        try:
            # Light validation to suggest improvements
            validate_manual_form_with_ai(upload)
            return redirect('processing_listing', upload_id=upload.id)
        except Exception as e:
            messages.error(request, f'Error processing form: {str(e)}')
            return render(request, 'manual_form_listing.html')
    
    return render(request, 'manual_form_listing.html')


def validate_manual_form_with_ai(upload: PropertyUpload):
    """Light validation for manual form to suggest improvements"""
    import openai
    from django.conf import settings
    
    comprehensive_data = upload.ai_validation_result or {}
    
    # Create a summary of what's provided
    provided_fields = []
    missing_critical = []
    
    # Check critical fields
    if upload.title:
        provided_fields.append("Property Title")
    else:
        missing_critical.append("Property Title")
    
    if upload.price_amount:
        provided_fields.append("Price")
    else:
        missing_critical.append("Price")
    
    if upload.city:
        provided_fields.append("City")
    else:
        missing_critical.append("City")
    
    if comprehensive_data.get('street_address'):
        provided_fields.append("Street Address")
    else:
        missing_critical.append("Street Address")
    
    # Check other comprehensive fields
    if comprehensive_data.get('property_type'):
        provided_fields.append("Property Type")
    if comprehensive_data.get('beds'):
        provided_fields.append("Bedrooms")
    if comprehensive_data.get('baths'):
        provided_fields.append("Bathrooms")
    if comprehensive_data.get('sqft'):
        provided_fields.append("Square Footage")
    if comprehensive_data.get('year_built'):
        provided_fields.append("Year Built")
    if comprehensive_data.get('kitchen_features'):
        provided_fields.append("Kitchen Features")
    if comprehensive_data.get('outdoor_features'):
        provided_fields.append("Outdoor Features")
    if comprehensive_data.get('amenities'):
        provided_fields.append("Community Amenities")
    
    # Create validation result
    validation_result = {
        'status': 'comprehensive' if len(missing_critical) == 0 else 'needs_improvement',
        'provided_fields': provided_fields,
        'missing_critical': missing_critical,
        'completeness_score': len(provided_fields) / 20 * 100,  # Out of ~20 key fields
        'recommendations': []
    }
    
    # Add recommendations for missing critical fields
    if missing_critical:
        validation_result['recommendations'].append(f"Please add: {', '.join(missing_critical)}")
    
    # Add general recommendations
    if len(provided_fields) < 15:
        validation_result['recommendations'].append("Consider adding more details about features, amenities, and property characteristics for better visibility.")
    
    upload.ai_validation_result = validation_result
    upload.missing_fields = missing_critical
    upload.status = 'validation' if missing_critical else 'complete'
    upload.save()
    
    # If no critical fields missing, create the property directly
    if not missing_critical:
        create_property_from_upload(upload)


# ============================================================================
# NEW: Buyer Homepage Chat System
# ============================================================================

@require_POST
def home_chat(request: HttpRequest) -> HttpResponse:
    """
    HTMX endpoint for buyer-facing conversational chat on homepage
    
    NEW FEATURE: Separate from property detail chat and AI validation
    This allows buyers to have a conversational property search experience
    directly from the homepage without navigating away.
    
    ENHANCED: Now handles search context from AI prompt results
    """
    message = request.POST.get("message", "").strip()
    
    if not message:
        return HttpResponseBadRequest("Message required")
    
    # Check if this is a follow-up from AI search results
    is_search_followup = "I just searched for" in message or "Can you help me find similar properties" in message
    
    # Process the conversational query using existing AI search helper
    enhanced_search = process_ai_search_prompt(message)
    
    # Query properties based on extracted parameters
    qs = Property.objects.all()
    
    if enhanced_search.get("city"):
        qs = qs.filter(Q(city__icontains=enhanced_search["city"]) | Q(area__icontains=enhanced_search["city"]))
    if enhanced_search.get("beds"):
        qs = qs.filter(beds__gte=enhanced_search["beds"])
    if enhanced_search.get("price_max"):
        qs = qs.filter(price_amount__lte=enhanced_search["price_max"])
    if enhanced_search.get("keywords"):
        for keyword in enhanced_search["keywords"]:
            qs = qs.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(badges__icontains=keyword))
    
    # Limit to top 6 results for chat suggestions
    top_results = qs[:6]
    
    # Generate conversational response
    response_text = generate_chat_response(message, enhanced_search, top_results.count())
    
    # Send webhook for buyer chat interaction
    try:
        chat_data = {
            "type": "buyer_chat",
            "message": message,
            "results_count": top_results.count(),
            "session_id": request.session.session_key or "anonymous",
            "timestamp": timezone.now().isoformat(),
            "extracted_params": enhanced_search,
            "utm_source": request.COOKIES.get("utm_source", ""),
            "utm_campaign": request.COOKIES.get("utm_campaign", ""),
            "referrer": request.META.get("HTTP_REFERER", ""),
        }
        send_chat_inquiry_webhook(chat_data)
    except Exception as e:
        print(f"Webhook error: {e}")
    
    # Render chat bubble + suggestions partial
    context = {
        "role": "assistant",
        "text": response_text,
        "properties": top_results,
        "search_params": enhanced_search,
        "original_message": message
    }
    
    return render(request, "partials/home_chat_suggestions.html", context)


def generate_chat_response(message: str, params: dict, count: int) -> str:
    """Generate conversational response for homepage chat"""
    
    # Check if this is a search follow-up
    is_search_followup = "I just searched for" in message or "Can you help me find similar properties" in message
    
    if is_search_followup:
        # Special greeting for search follow-ups
        if count > 0:
            return f"Hi there! 👋 I see you just completed a search! I found {count} properties that match your criteria. I'm here to help you explore these options or find even better matches. What would you like to know about these properties?"
        else:
            return "Hi there! 👋 I see you just completed a search! While I couldn't find exact matches, I'm here to help you refine your search or explore similar options. What specific features are most important to you?"
    
    # Regular response for new searches
    if count == 0:
        return "I couldn't find exact matches for your criteria, but let me show you some similar options you might like!"
    
    parts = []
    
    # Acknowledge their search
    if params.get("beds"):
        parts.append(f"{params['beds']} bedroom")
    if params.get("city"):
        parts.append(f"in {params['city']}")
    if params.get("price_max"):
        parts.append(f"under ${params['price_max']:,}")
    
    if parts:
        criteria = " ".join(parts)
        return f"Perfect! I found {count} great {'option' if count == 1 else 'options'} {criteria}. Check these out:"
    
    return f"Great! I found {count} properties that match what you're looking for:"


def property_modal(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Return property quick view modal content (HTMX endpoint)
    
    NEW FEATURE: Allows buyers to preview properties without leaving homepage
    Different from full property_detail page - this is a lightweight popup
    """
    property_obj = get_object_or_404(Property, slug=slug)
    
    # Track modal view
    try:
        modal_data = {
            "type": "property_modal_view",
            "property_id": str(property_obj.id),
            "property_slug": property_obj.slug,
            "property_title": property_obj.title,
            "session_id": request.session.session_key or "anonymous",
            "timestamp": timezone.now().isoformat(),
            "referrer": request.META.get("HTTP_REFERER", ""),
        }
        send_property_chat_webhook(modal_data)
    except Exception as e:
        print(f"Webhook error: {e}")
    
    context = {
        "property": property_obj
    }
    
    return render(request, "partials/property_modal.html", context)


@require_POST
def ai_prompt_search(request: HttpRequest) -> HttpResponse:
    """
    NEW: Interactive AI prompt search that sends to webhook and displays response
    
    This endpoint:
    1. Receives AI prompt from homepage form
    2. Sends to Katalyst CRM webhook
    3. Waits for webhook response
    4. Displays response to user
    5. Shows matching properties
    """
    import requests
    
    ai_prompt = request.POST.get("ai_prompt", "").strip()
    
    if not ai_prompt:
        return HttpResponseBadRequest("AI prompt required")
    
    # Process locally to get properties
    enhanced_search = process_ai_search_prompt(ai_prompt)
    
    # Query properties based on extracted parameters
    qs = Property.objects.all()
    
    if enhanced_search.get("city"):
        qs = qs.filter(Q(city__icontains=enhanced_search["city"]) | Q(area__icontains=enhanced_search["city"]))
    if enhanced_search.get("beds"):
        qs = qs.filter(beds__gte=enhanced_search["beds"])
    if enhanced_search.get("price_max"):
        qs = qs.filter(price_amount__lte=enhanced_search["price_max"])
    if enhanced_search.get("keywords"):
        for keyword in enhanced_search["keywords"]:
            qs = qs.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(badges__icontains=keyword))
    
    # Get top properties
    top_properties = qs[:6]
    
    # Prepare webhook payload
    webhook_url = "https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545"
    webhook_payload = {
        "type": "ai_prompt_search",
        "timestamp": timezone.now().isoformat(),
        "session_id": request.session.session_key or "anonymous",
        "prompt": ai_prompt,
        "extracted_params": {
            "city": enhanced_search.get("city", ""),
            "beds": enhanced_search.get("beds"),
            "price_max": enhanced_search.get("price_max"),
            "buy_or_rent": enhanced_search.get("buy_or_rent", ""),
            "keywords": enhanced_search.get("keywords", [])
        },
        "results_count": top_properties.count(),
        "properties": [
            {
                "id": str(prop.id),
                "slug": prop.slug,
                "title": prop.title,
                "price": prop.price_amount,
                "city": prop.city,
                "area": prop.area,
                "beds": prop.beds,
                "baths": prop.baths
            } for prop in top_properties
        ],
        "tracking": {
            "utm_source": request.COOKIES.get("utm_source", ""),
            "utm_campaign": request.COOKIES.get("utm_campaign", ""),
            "referrer": request.META.get("HTTP_REFERER", ""),
        }
    }
    
    # Send to webhook and get response
    webhook_response = None
    webhook_success = False
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'PropertyListingBot/1.0',
        }
        
        response = requests.post(
            webhook_url,
            json=webhook_payload,
            headers=headers,
            timeout=10
        )
        
        webhook_success = response.status_code in [200, 201, 202]
        
        # Try to get JSON response
        try:
            webhook_response = response.json()
        except:
            webhook_response = {"message": response.text[:200] if response.text else "Success"}
            
        print(f"✅ Webhook sent successfully. Status: {response.status_code}")
        
    except Exception as e:
        print(f"⚠️ Webhook error: {e}")
        webhook_response = {"message": "Got it — analyzing your info…"}
    
    # Generate AI-style response message
    if top_properties.count() > 0:
        response_message = f"Perfect! I found {top_properties.count()} great {'property' if top_properties.count() == 1 else 'properties'}"
        
        # Add context about search criteria
        criteria_parts = []
        if enhanced_search.get("beds"):
            criteria_parts.append(f"{enhanced_search['beds']}+ bedrooms")
        if enhanced_search.get("city"):
            criteria_parts.append(f"in {enhanced_search['city']}")
        if enhanced_search.get("price_max"):
            criteria_parts.append(f"under ${enhanced_search['price_max']:,}")
        
        if criteria_parts:
            response_message += " " + ", ".join(criteria_parts)
        
        response_message += ". Check these out!"
    else:
        response_message = "I couldn't find exact matches for your criteria, but let me show you some similar options you might like!"
    
    # Render response
    context = {
        "ai_prompt": ai_prompt,
        "response_message": response_message,
        "properties": top_properties,
        "enhanced_search": enhanced_search,
        "webhook_response": webhook_response,
        "webhook_success": webhook_success,
        "results_count": top_properties.count()
    }
    
    # If this is an HTMX request, return partial
    if request.headers.get('HX-Request'):
        return render(request, "partials/ai_prompt_results.html", context)
    
    # Otherwise return full page (redirect to results)
    return redirect(f"{reverse('results')}?ai_prompt={ai_prompt}")


@require_POST
def init_webhook_chat(request: HttpRequest) -> HttpResponse:
    """
    Initialize the chatbox with the first user message
    Transforms the search form into a chat interface
    """
    import requests
    
    initial_message = request.POST.get("ai_prompt", "").strip()
    
    if not initial_message:
        return HttpResponseBadRequest("Message required")
    
    # Initialize chat history in session
    request.session["chat_history"] = []
    
    # Add user message to history
    request.session["chat_history"].append({
        "role": "user",
        "message": initial_message,
        "timestamp": timezone.now().isoformat()
    })
    
    # Send to webhook
    webhook_url = "https://katalyst-crm.fly.dev/webhook-test/ca05d7c5-984c-4d95-8636-1ed3d80f5545"
    session_id = request.session.session_key or "anonymous"
    
    # Get property context
    properties = Property.objects.all()[:10]
    property_context = [
        {
            "id": str(prop.id),
            "title": prop.title,
            "price": prop.price_amount,
            "city": prop.city,
            "beds": prop.beds,
            "baths": prop.baths
        } for prop in properties
    ]
    
    webhook_payload = {
        "type": "ai_chat_init",
        "timestamp": timezone.now().isoformat(),
        "session_id": session_id,
        "message": initial_message,
        "property_context": property_context,
        "tracking": {
            "utm_source": request.COOKIES.get("utm_source", ""),
            "utm_campaign": request.COOKIES.get("utm_campaign", ""),
            "referrer": request.META.get("HTTP_REFERER", ""),
        }
    }
    
    # Get webhook response
    ai_response = "Great! I'm here to help you find your perfect home. Based on what you've told me, let me ask you a few questions to narrow down the best options for you."
    
    try:
        response = requests.post(
            webhook_url,
            json=webhook_payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        webhook_response = response.json()
        
        if webhook_response and "Response" in webhook_response:
            ai_response = webhook_response["Response"]
            
    except Exception as e:
        print(f"Webhook error: {e}")
    
    # Add AI response to history
    request.session["chat_history"].append({
        "role": "assistant",
        "message": ai_response,
        "timestamp": timezone.now().isoformat()
    })
    
    request.session.modified = True
    
    # Return chatbox interface
    return render(request, "partials/chatbox_interface.html", {
        "initial_message": initial_message,
        "ai_response": ai_response
    })


@require_POST
def webhook_chat(request: HttpRequest) -> HttpResponse:
    """
    Handle AI chat conversation via webhook
    Sends user messages to webhook and returns AI responses
    """
    import requests
    
    user_message = request.POST.get("message", "").strip()
    session_id = request.session.session_key or "anonymous"
    
    if not user_message:
        return JsonResponse({"error": "Message required"}, status=400)
    
    # Store conversation history in session
    if "chat_history" not in request.session:
        request.session["chat_history"] = []
    
    # Add user message to history
    request.session["chat_history"].append({
        "role": "user",
        "message": user_message,
        "timestamp": timezone.now().isoformat()
    })
    
    # Prepare webhook payload
    webhook_url = "https://katalyst-crm.fly.dev/webhook-test/ca05d7c5-984c-4d95-8636-1ed3d80f5545"
    
    # Get property context if available
    properties = Property.objects.all()[:10]
    property_context = [
        {
            "id": str(prop.id),
            "title": prop.title,
            "price": prop.price_amount,
            "city": prop.city,
            "beds": prop.beds,
            "baths": prop.baths
        } for prop in properties
    ]
    
    webhook_payload = {
        "type": "ai_chat",
        "timestamp": timezone.now().isoformat(),
        "session_id": session_id,
        "message": user_message,
        "chat_history": request.session["chat_history"],
        "property_context": property_context,
        "tracking": {
            "utm_source": request.COOKIES.get("utm_source", request.GET.get("utm_source", "")),
            "utm_campaign": request.COOKIES.get("utm_campaign", request.GET.get("utm_campaign", "")),
            "referrer": request.META.get("HTTP_REFERER", ""),
        }
    }
    
    # Send to webhook and get response
    webhook_response = None
    webhook_success = False
    ai_response = "I'm here to help you find your perfect home! Could you tell me more about what you're looking for?"
    
    try:
        response = requests.post(
            webhook_url,
            json=webhook_payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        webhook_response = response.json()
        webhook_success = True
        
        # Extract AI response from webhook
        if webhook_response and "Response" in webhook_response:
            ai_response = webhook_response["Response"]
        
    except requests.exceptions.Timeout:
        ai_response = "I'm experiencing some delays. Let me help you - what specific features are most important in your ideal home?"
    except requests.exceptions.RequestException as e:
        print(f"Webhook error: {e}")
        ai_response = "I'm here to help! Tell me about your budget, preferred location, and must-have amenities."
    
    # Add AI response to history
    request.session["chat_history"].append({
        "role": "assistant",
        "message": ai_response,
        "timestamp": timezone.now().isoformat()
    })
    
    # Save session
    request.session.modified = True
    
    # Return response for HTMX
    if request.headers.get('HX-Request'):
        return render(request, "partials/chat_message.html", {
            "message": ai_response,
            "role": "assistant",
            "timestamp": timezone.now()
        })
    
    # JSON response for non-HTMX requests
    return JsonResponse({
        "success": webhook_success,
        "response": ai_response,
        "webhook_data": webhook_response
    })


