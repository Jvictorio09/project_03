from __future__ import annotations

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db import connection

from .models import Property, Lead
from .forms import LeadForm


def home(request: HttpRequest) -> HttpResponse:
    top_picks = Property.objects.all()[:6]
    return render(request, "home.html", {"top_picks": top_picks})


def results(request: HttpRequest) -> HttpResponse:
    qs = Property.objects.all()
    q = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    beds = request.GET.get("beds", "").strip()
    price_max = request.GET.get("price_max", "").strip()

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(badges__icontains=q) | Q(city__icontains=q))
    if city:
        qs = qs.filter(Q(city__iexact=city) | Q(area__icontains=city))
    if beds and beds.isdigit():
        qs = qs.filter(beds__gte=int(beds))
    if price_max and price_max.isdigit():
        qs = qs.filter(price_amount__lte=int(price_max))

    return render(request, "results.html", {"properties": qs, "count": qs.count()})


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


def simple_answer(prop: Property, text: str) -> str:
    """Simple rule-based responder for property questions"""
    text = text.lower()
    
    # Price questions
    if any(word in text for word in ["price", "rent", "cost", "monthly"]):
        return f"The monthly rent is ₱{prop.price_amount:,} PHP."
    
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


