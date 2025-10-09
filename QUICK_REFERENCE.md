# Quick Reference Guide

## 🔍 Function Index

### **Search & Discovery**
- `home()` - Display homepage with top 6 properties
- `results()` - Handle search (traditional + AI prompt)
- `process_ai_search_prompt()` - Parse natural language search queries

### **🆕 Buyer Homepage Chat (NEW)**
- `home_chat()` - HTMX endpoint for conversational homepage chat
- `property_modal()` - Return property quick view modal (popup)
- `generate_chat_response()` - Generate friendly chat responses

### **Property Details**
- `property_detail()` - Display individual property page
- `property_chat()` - HTMX chat endpoint for property Q&A
- `simple_answer()` - Rule-based chatbot responses

### **Lead Management**
- `lead_submit()` - Handle lead form submission
- `thanks()` - Thank you page after submission
- `book()` - Booking page

### **Property Upload - Entry Points**
- `listing_choice()` - Choose upload method (AI vs Manual)
- `upload_listing()` - Simple upload form
- `ai_prompt_listing()` - AI prompt-based upload
- `manual_form_listing()` - Comprehensive manual form

### **Property Upload - AI Processing**
- `validate_property_with_ai()` - Initial OpenAI validation
- `process_ai_prompt_with_validation()` - Process AI prompt uploads
- `validate_manual_form_with_ai()` - Light validation for manual forms
- `processing_listing()` - Processing status page
- `validation_chat()` - Interactive validation chat

### **Property Upload - AI Assistance**
- `get_ai_validation_response()` - Get AI response in validation chat
- `get_specific_fallback_response()` - Fallback responses when AI fails
- `check_validation_complete()` - Check if validation is done
- `consolidate_property_information()` - Create final description
- `create_property_from_upload()` - Create final Property object

### **Data Extraction Helpers**
- `extract_basic_info_from_description()` - Extract structured data from text
- `generate_missing_fields_list()` - Identify missing fields

### **Admin & System**
- `dashboard()` - Internal dashboard with search/filter/sort
- `health_check()` - Railway health check endpoint

### **Webhooks**
- `send_chat_inquiry_webhook()` - Send lead/chat data to CRM
- `send_property_listing_webhook()` - Send new listing to CRM
- `send_property_chat_webhook()` - Send property chat to CRM
- `send_prompt_search_webhook()` - Send search analytics to CRM
- `send_webhook()` - Base webhook sender

---

## 📋 Common Tasks

### **Add a New Property Manually**
```python
from myApp.models import Property

Property.objects.create(
    title="Beautiful 2BR Condo",
    slug="beautiful-2br-condo",
    description="...",
    price_amount=3500,
    city="Los Angeles",
    area="Downtown",
    beds=2,
    baths=2,
    parking=True,
    hero_image="https://...",
)
```

### **Query Properties**
```python
# Get all properties in LA
properties = Property.objects.filter(city="Los Angeles")

# Get properties under $3000 with 2+ beds
properties = Property.objects.filter(
    price_amount__lte=3000,
    beds__gte=2
)

# Search by keyword
from django.db.models import Q
properties = Property.objects.filter(
    Q(title__icontains="modern") | 
    Q(description__icontains="modern")
)
```

### **Access Lead Data**
```python
from myApp.models import Lead

# Get all recent leads
leads = Lead.objects.all()[:10]

# Filter by intent
renters = Lead.objects.filter(buy_or_rent="rent")
buyers = Lead.objects.filter(buy_or_rent="buy")

# Search leads
leads = Lead.objects.filter(name__icontains="John")
```

### **Check PropertyUpload Status**
```python
from myApp.models import PropertyUpload

# Get uploads in validation
uploads = PropertyUpload.objects.filter(status='validation')

# Get completed uploads
completed = PropertyUpload.objects.filter(status='complete')

# Check specific upload
upload = PropertyUpload.objects.get(id='uuid-here')
print(upload.missing_fields)
print(upload.validation_chat_history)
```

---

## 🔗 URL Patterns Quick Reference

```
/                              → Home
/list                          → Search results
/list?ai_prompt=...           → AI search
/list?city=...&beds=...       → Traditional search
/property/{slug}/             → Property detail
/property/{slug}/chat         → Chat endpoint (POST)
/lead/submit                  → Lead form (POST)
/dashboard                     → Internal dashboard
/listing-choice/              → Choose upload method
/ai-prompt-listing/           → AI upload
/manual-form-listing/         → Manual upload
/processing/{uuid}/           → Processing status
/validation/{uuid}/           → Validation chat
/thanks?lead={uuid}           → Thank you
/health/                      → Health check
/chat/home/                   → 🆕 Homepage chat (POST, HTMX)
/p/{slug}/modal/              → 🆕 Property quick view modal (GET, HTMX)
```

---

## 🎨 Template Variables Reference

### **results.html**
- `properties` - QuerySet of Property objects
- `count` - Total results
- `ai_prompt` - User's AI search prompt
- `search_type` - "ai_prompt" or "traditional"

### **property_detail.html**
- `property` - Property object

### **validation_chat.html**
- `upload` - PropertyUpload object
- `chat_history` - List of chat messages
- `completion_percentage` - 0-100
- `validation_status` - Dict of section statuses
- `missing_fields` - List of missing field names

### **dashboard.html**
- `properties` - Paginated properties
- `cities` - Distinct city list
- `total_count` - Total properties
- `current_filters` - Dict of active filters

---

## 🔧 Configuration

### **settings.py Key Settings**
```python
ALLOWED_HOSTS = ['project03-production.up.railway.app', '127.0.0.1', 'localhost']
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### **Webhook URLs**
```python
CHAT_INQUIRY_WEBHOOK = "https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545ponse"
PROPERTY_LISTING_WEBHOOK = "https://katalyst-crm.fly.dev/webhook-test/7e36f0ef-e0b2-498d-886c-f06bef9afd80"
```

---

## 🐛 Debugging Tips

### **Check if webhooks are working:**
Look for console output:
```
Webhook sent successfully to https://...
# or
Failed to send webhook to https://...: [error]
```

### **View AI validation results:**
```python
upload = PropertyUpload.objects.get(id='uuid')
print(upload.ai_validation_result)
print(upload.missing_fields)
print(upload.validation_chat_history)
```

### **Test AI functions without full flow:**
```python
from myApp.views import process_ai_search_prompt

result = process_ai_search_prompt("2 bedroom in Los Angeles under $3000")
print(result)
# {'city': 'Los Angeles', 'beds': 2, 'price_max': 3000, ...}
```

### **Test chatbot responses:**
```python
from myApp.views import simple_answer
from myApp.models import Property

prop = Property.objects.first()
response = simple_answer(prop, "how much is rent?")
print(response)
```

---

## 📊 Model Field Quick Reference

### **Property**
```python
id, slug, title, description, price_amount, city, area, 
beds, baths, floor_area_sqm, parking, hero_image, badges,
affiliate_source, commissionable, created_at
```

### **Lead**
```python
id, name, phone, email, buy_or_rent, budget_max, beds,
areas, interest_ids, utm_source, utm_campaign, referrer,
consent_contact, created_at
```

### **PropertyUpload**
```python
id, property, status, title, description, price_amount,
city, area, beds, baths, hero_image, ai_validation_result,
missing_fields, validation_chat_history, 
consolidated_information, created_at, updated_at
```

---

## 🎯 Template Tags Usage

```django
{% load extras %}

{{ 3500|peso }}                    {# $3,500 #}
{{ "LA,NYC"|splitcsv }}            {# ['LA', 'NYC'] #}
{{ " text "|strip }}               {# "text" #}
{{ beds|pluralize }}               {# "s" if beds != 1 #}
{{ "Los Angeles"|urlencode }}      {# "Los%20Angeles" #}
{{ "a-b-c"|split:"-" }}           {# ['a', 'b', 'c'] #}
```

---

## 🚀 Common Development Commands

```bash
# Run development server
python manage.py runserver

# Make migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Access Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test
```

---

## 📝 Real Estate Validation Checklist (Used by AI)

1. 🏡 **Property Identification** - Type, status, agent info
2. 📍 **Location Details** - Address, neighborhood, schools
3. 📐 **Lot & Building** - Size, year built, parking
4. 🛋 **Interior Features** - Beds, baths, kitchen, HVAC
5. 🏢 **Property Features** - Outdoor, amenities, views
6. 💰 **Financial Info** - Price, taxes, HOA, utilities
7. 📜 **Legal Info** - Title, occupancy, zoning
8. 🖼 **Media Assets** - Photos, floor plans, tours
9. 📎 **Documentation** - Disclosures, inspections, permits

---

This quick reference should help you navigate the codebase efficiently!

