# 🔎 Diagnostic Snapshot - KaTek AI System

## 1) Multi-tenancy & Data Model (ERD or headers)

### **❌ CRITICAL ISSUE: NO MULTI-TENANCY IMPLEMENTED**

**Current Model Headers:**
```python
# myApp/models.py

class Property(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price_amount = models.IntegerField()
    city = models.CharField(max_length=64)
    area = models.CharField(max_length=64, blank=True)
    beds = models.IntegerField(default=1)
    baths = models.IntegerField(default=1)
    floor_area_sqm = models.IntegerField(default=0)
    parking = models.BooleanField(default=False)
    hero_image = models.URLField(blank=True)
    badges = models.CharField(max_length=128, blank=True)
    affiliate_source = models.CharField(max_length=64, blank=True)
    commissionable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # ❌ MISSING: company = models.ForeignKey(Company, ...)

class Lead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    buy_or_rent = models.CharField(max_length=8, choices=BOR_CHOICES)
    budget_max = models.IntegerField(null=True, blank=True)
    beds = models.IntegerField(null=True, blank=True)
    areas = models.CharField(max_length=256, blank=True)
    interest_ids = models.CharField(max_length=512, blank=True)
    utm_source = models.CharField(max_length=64, blank=True)
    utm_campaign = models.CharField(max_length=64, blank=True)
    referrer = models.URLField(blank=True)
    consent_contact = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # ❌ MISSING: company = models.ForeignKey(Company, ...)

class PropertyUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.OneToOneField(Property, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    # ... other fields ...
    # ❌ MISSING: company = models.ForeignKey(Company, ...)
```

**❌ MISSING: Company Model**
```python
# NEEDS TO BE CREATED:
class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo = models.URLField(blank=True)
    primary_color = models.CharField(max_length=7, default='#6D28D9')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Note: Where company_id comes from**: ❌ **NOT IMPLEMENTED**
- No session/middleware for company scoping
- No queryset filtering by company
- All data is global (not tenant-isolated)

**Vectors: Index/namespace strategy per org**: ❌ **NOT IMPLEMENTED**
- No vector database integration
- No embedding storage
- No per-company namespace strategy

---

## 2) Auth, Access Control, Wizard Gating

### **❌ CRITICAL ISSUE: AUTHENTICATION SYSTEM INCOMPLETE**

**Settings.py Configuration:**
```python
# myProject/settings.py
AUTH_USER_MODEL = 'auth.User'  # ❌ Using default User model
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
LOGIN_URL = 'login'  # ❌ Not configured
```

**Guarded Views (Only 5 out of 58 views protected):**
```python
# myApp/views.py
@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Main Dashboard with metrics and overview"""
    # ❌ Uses mock data, no company scoping

@login_required
def setup_wizard(request: HttpRequest) -> HttpResponse:
    """4-step setup wizard for new users"""
    # ❌ Backend not implemented

@login_required
def properties(request: HttpRequest) -> HttpResponse:
    """Properties management page with table, filters, and bulk actions"""
    # ❌ Uses mock data, no company scoping

@login_required
def chat_agent(request: HttpRequest) -> HttpResponse:
    """Chat agent configuration page with live simulation"""
    # ❌ Uses mock data, no company scoping

@login_required
def leads(request: HttpRequest) -> HttpResponse:
    """Leads CRM page with table, filters, and lead drawer"""
    # ❌ Uses mock data, no company scoping

@login_required
def campaigns(request: HttpRequest) -> HttpResponse:
    """Campaigns management page with creation and analytics"""
    # ❌ Uses mock data, no company scoping

@login_required
def analytics(request: HttpRequest) -> HttpResponse:
    """Analytics dashboard with charts, insights, and performance metrics"""
    # ❌ Uses mock data, no company scoping

@login_required
def settings(request: HttpRequest) -> HttpResponse:
    """User settings page"""
    # ❌ Uses mock data, no company scoping
```

**❌ MISSING: 51 views have NO authentication protection**
- All public-facing views (home, search, property detail, chat, etc.)
- All upload and validation views
- All webhook endpoints

---

## 3) URL Map + Real vs Mock

### **URL Pattern Analysis (58 Total Routes)**

**✅ REAL FUNCTIONALITY (12 routes)**
```
/                           [real] - Homepage with search
/list                       [real] - Property search results  
/property/<slug>/            [real] - Property detail page
/property/<slug>/chat        [real] - Property chat interface
/property/<slug>/chat-simple [real] - Simple property chat
/property/<slug>/chat-ai     [real] - AI property chat
/property/<slug>/modal       [real] - Property modal view
/home-chat                   [real] - Homepage chat widget
/listing-choice/             [real] - Upload method selection
/ai-prompt-listing/          [real] - AI upload form
/manual-form-listing/        [real] - Manual upload form
/upload-listing/             [real] - File upload handler
```

**🚧 PARTIALLY REAL (8 routes)**
```
/processing/<uuid>/           [real] - Processing page (UI only)
/validation/<uuid>/          [real] - AI validation chat (UI only)
/lead/submit                 [real] - Lead form submission (basic)
/book                        [real] - Booking page (basic)
/thanks                      [real] - Thank you page (basic)
/dashboard                   [mock] - Dashboard (mock data)
/health/                     [real] - Health check endpoint
/search/ai-prompt/           [real] - AI search endpoint
```

**❌ MOCK/INCOMPLETE (38 routes)**
```
/landing/                    [mock] - Landing page (UI only)
/signup/                     [mock] - Signup form (UI only)
/login/                      [mock] - Login form (UI only)
/logout/                     [mock] - Logout handler (UI only)
/password-reset/             [mock] - Password reset (UI only)
/password-reset-confirm/     [mock] - Password reset confirm (UI only)
/setup/                      [mock] - Setup wizard (Step 1 only)
/properties/                 [mock] - Properties management (mock data)
/chat-agent/                 [mock] - Chat agent config (mock data)
/leads/                      [mock] - Leads CRM (mock data)
/campaigns/                  [mock] - Campaigns system (mock data)
/analytics/                  [mock] - Analytics dashboard (mock data)
/chat/                       [mock] - End-user chat (mock data)
/settings/                   [mock] - Settings page (mock data)
/chat/webhook/init/          [mock] - Webhook chat init (basic)
/chat/webhook/               [mock] - Webhook chat handler (basic)
/api/properties/titles/      [real] - Property titles API (basic)
/ai-validation/init/          [mock] - AI validation init (basic)
/ai-validation/chat/         [mock] - AI validation chat (basic)
```

---

## 4) Ingestion → Enrichment → Search

### **Function Signatures & Implementation**

**✅ WORKING FUNCTIONS:**
```python
def upload_listing(request: HttpRequest) -> HttpResponse:
    """Handle property upload form"""
    # ✅ Real implementation - saves to PropertyUpload model
    # ✅ Cloudinary integration for images
    # ✅ Form validation and error handling

def validate_property_with_ai(upload: PropertyUpload):
    """Send property data to OpenAI for validation"""
    # ✅ Real implementation - calls OpenAI API
    # ✅ 9-section validation checklist
    # ✅ JSON response parsing and storage

def create_property_from_upload(upload: PropertyUpload):
    """Create Property object from validated upload"""
    # ✅ Real implementation - creates Property from PropertyUpload
    # ✅ Slug generation and conflict resolution
    # ✅ Data consolidation and cleanup
```

**❌ MISSING: Narrative + Embeddings Storage**
```python
# NOT IMPLEMENTED:
class Property(models.Model):
    # ... existing fields ...
    narrative = models.TextField(blank=True)  # ❌ MISSING
    embeddings = models.JSONField(default=list, blank=True)  # ❌ MISSING
    last_updated = models.DateTimeField(auto_now=True)  # ❌ MISSING
    source = models.CharField(max_length=64, default='manual')  # ❌ MISSING
    neighborhood_avg = models.IntegerField(null=True, blank=True)  # ❌ MISSING
    estimate = models.IntegerField(null=True, blank=True)  # ❌ MISSING
```

**❌ MISSING: Search Implementation**
```python
# Current search is basic Django ORM only:
def results(request: HttpRequest) -> HttpResponse:
    qs = Property.objects.all()  # ❌ No company scoping
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(city__icontains=q) |
            Q(area__icontains=q)
        )
    # ❌ No GIN/trigram index
    # ❌ No vector search
    # ❌ No AI-powered search
```

**❌ MISSING: Enrichment Pipeline**
- No automated data enrichment
- No neighborhood average calculation
- No price estimation
- No narrative generation
- No embedding creation

---

## 5) Lead Capture → Autoresponder → Webhook

### **Lead Submit Implementation**
```python
def lead_submit(request: HttpRequest) -> HttpResponse:
    """Handle lead form submission"""
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    
    form = LeadForm(request.POST)
    if form.is_valid():
        lead = form.save()
        # ✅ Real implementation - saves to Lead model
        
        # ✅ Webhook integration
        send_chat_inquiry_webhook({
            'type': 'lead_submission',
            'lead_id': str(lead.id),
            'name': lead.name,
            'phone': lead.phone,
            'email': lead.email,
            'buy_or_rent': lead.buy_or_rent,
            'budget_max': lead.budget_max,
            'beds': lead.beds,
            'areas': lead.areas,
            'utm_source': lead.utm_source,
            'utm_campaign': lead.utm_campaign,
            'referrer': lead.referrer,
            'consent_contact': lead.consent_contact,
            'created_at': lead.created_at.isoformat(),
        })
        
        return JsonResponse({'success': True, 'lead_id': str(lead.id)})
    else:
        return JsonResponse({'success': False, 'errors': form.errors})
```

**❌ MISSING: Dedupe Rule Location**
```python
# NOT IMPLEMENTED - No deduplication logic
# Should check for existing leads with same email+phone within 24h
```

**✅ Webhook Signing (Basic Implementation)**
```python
# myApp/webhook.py
def send_webhook(url: str, data: Dict[str, Any]) -> bool:
    """Send data to a webhook URL"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'PropertyListingBot/1.0',
            'Origin': 'https://project03-production.up.railway.app',
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Webhook sent successfully to {url}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send webhook to {url}: {str(e)}")
        return False
```

**❌ MISSING: Webhook Signing**
- No HMAC signature verification
- No retry logic with exponential backoff
- No webhook event logging
- No dead letter queue

**Environment Variables in Use:**
```bash
# ENV_EXAMPLE.txt
OPENAI_API_KEY=sk-your-openai-api-key-here
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret
SECRET_KEY=your-django-secret-key-here
DEBUG=True
```

**❌ MISSING: Additional Environment Variables**
```bash
# NOT CONFIGURED:
RESEND_API_KEY=your-resend-api-key
RESEND_FROM=noreply@katek.ai
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
```

---

## 🧭 Decision Toggles (fill Yes/No/Undecided)

**Tenancy = row-level FK to Company (not separate DB)**: ❌ **NO** - Not implemented

**Vectors = per-company namespace (not shared index)**: ❌ **NO** - Not implemented

**Framework = Django templates now; DRF later**: ✅ **YES** - Current approach

**Queue = Use RQ + Redis for enrichment/webhooks now (n8n later)**: ❌ **NO** - Not implemented

**Email = Transactional only now (Resend/SendGrid)**: ✅ **YES** - Resend configured

**Channels = Web chat first; FB/IG later (after App Review)**: ✅ **YES** - Web chat implemented

---

## 🧩 Connectivity Matrix (buttons, modals, actions)

| UI Element (selector/text) | Expected Action | Route/HTMX Endpoint | Method | Payload | Feature Flag | Status |
|----------------------------|----------------|-------------------|--------|---------|--------------|---------|
| Dashboard → "View All Properties" | Navigate | /properties | GET | – | properties_v1 | ⛔ Not wired |
| Dashboard → "View All Leads" | Navigate | /leads | GET | – | leads_crud | ⛔ Not wired |
| Dashboard → "Create Campaign" | Navigate | /campaigns | GET | – | campaigns_v1 | ⛔ Not wired |
| Dashboard → "View Analytics" | Navigate | /analytics | GET | – | analytics_events | ⛔ Not wired |
| Properties → "Add Property" | Open modal | #modal-add-property | n/a | – | properties_v1 | ⛔ Not wired |
| Properties → "Bulk Actions" | Dropdown | /properties/bulk | POST | {action, ids} | properties_v1 | ⛔ Not wired |
| Properties → "Sync Estimates" | POST | /properties/sync | POST | {property_ids} | properties_v1 | ⛔ Not wired |
| Properties → "Publish to Site" | POST | /properties/publish | POST | {property_ids} | properties_v1 | ⛔ Not wired |
| Properties → "Archive" | POST | /properties/archive | POST | {property_ids} | properties_v1 | ⛔ Not wired |
| Leads → "Assign to Agent" | POST | /leads/assign | POST | {lead_id, user_id} | leads_crud | ⛔ Not wired |
| Leads → "Mark as Contacted" | POST | /leads/contact | POST | {lead_id} | leads_crud | ⛔ Not wired |
| Leads → "Schedule Follow-up" | POST | /leads/followup | POST | {lead_id, date} | leads_crud | ⛔ Not wired |
| Campaigns → "Create Campaign" | Open drawer | /campaigns/new | GET | – | campaigns_v1 | ⛔ Not wired |
| Campaigns → "Send Email" | POST | /campaigns/send | POST | {campaign_id} | campaigns_v1 | ⛔ Not wired |
| Campaigns → "Schedule Campaign" | POST | /campaigns/schedule | POST | {campaign_id, date} | campaigns_v1 | ⛔ Not wired |
| Analytics → "Export Report" | POST | /analytics/export | POST | {format, date_range} | analytics_events | ⛔ Not wired |
| Analytics → "Refresh Data" | POST | /analytics/refresh | POST | – | analytics_events | ⛔ Not wired |
| Chat Agent → "Save Configuration" | POST | /chat-agent/save | POST | {config} | chat_agent_v1 | ⛔ Not wired |
| Chat Agent → "Test Agent" | POST | /chat-agent/test | POST | {message} | chat_agent_v1 | ⛔ Not wired |
| Chat Agent → "Deploy Agent" | POST | /chat-agent/deploy | POST | {config} | chat_agent_v1 | ⛔ Not wired |
| Settings → "Save Settings" | POST | /settings/save | POST | {settings} | settings_v1 | ⛔ Not wired |
| Settings → "Test Integration" | POST | /settings/test | POST | {integration} | settings_v1 | ⛔ Not wired |
| Setup → "Continue" (Step 2) | POST | /setup/step-2 | POST | {config} | setup_wizard | ⛔ Not wired |
| Setup → "Continue" (Step 3) | POST | /setup/step-3 | POST | {config} | setup_wizard | ⛔ Not wired |
| Setup → "Continue" (Step 4) | POST | /setup/step-4 | POST | {config} | setup_wizard | ⛔ Not wired |

**Rule: If Feature Flag == False, disable with tooltip: "Coming soon—enabled in staging."**

---

## 🪟 Modal/HTMX Wiring Checklist (fix broken modals fast)

### **❌ CRITICAL ISSUES:**

**Unique IDs**: ❌ **NOT IMPLEMENTED**
- No modal system implemented
- No unique IDs for modals
- No role="dialog" elements

**Open triggers**: ❌ **NOT IMPLEMENTED**
- No data-modal-target attributes
- No HTMX modal loading
- No modal trigger buttons

**Show/hide JS**: ❌ **NOT IMPLEMENTED**
```javascript
// NOT IMPLEMENTED - No centralized modal JS
document.addEventListener('click', e=>{
  const btn=e.target.closest('[data-modal-target]'); 
  if(btn){document.querySelector(btn.dataset.modalTarget)?.classList.remove('hidden')}
  const close=e.target.closest('[data-modal-close]'); 
  if(close){close.closest('[role="dialog"]')?.classList.add('hidden')}
});
```

**Focus trap + ESC**: ❌ **NOT IMPLEMENTED**
- No focus management
- No keyboard navigation
- No accessibility features

**HTMX targets**: ❌ **NOT IMPLEMENTED**
- No HTMX modal loading
- No .modal-body targets
- No content swapping

**CSRF**: ❌ **NOT IMPLEMENTED**
- No CSRF tokens in modal forms
- No CSRF_COOKIE verification

**Aria**: ❌ **NOT IMPLEMENTED**
- No aria-modal="true"
- No aria-labelledby
- No keyboard behavior

---

## 🏁 Sanity Probes (run now; paste results under each)

### **Auth gate**
```bash
curl -I http://localhost:8000/dashboard
# Expected: 302 to /login when anonymous
# Actual: ❌ 500 Internal Server Error (no login URL configured)
```

### **Company scoping**
```bash
# Visit /properties as two users; confirm queries filter by company_id
# Actual: ❌ NOT IMPLEMENTED - No company scoping, no user system
```

### **Search reality**
```bash
# Create one property in UI → appears in /list within 1s
# Actual: ✅ WORKS - Property creation and search functional

# Search "Makati" → excludes non-Makati
# Actual: ✅ WORKS - Basic text search functional
```

### **Lead dedupe & webhook**
```bash
# Submit same email+property twice within 24h → expect 409/validation error
# Actual: ❌ NOT IMPLEMENTED - No deduplication logic

# Verify webhook retries/backoff log (even if stub)
# Actual: ✅ WORKS - Webhook logging functional
```

### **Narrative freshness**
```bash
# Change price → re-enrich → detail shows updated last_updated + source
# Actual: ❌ NOT IMPLEMENTED - No narrative system, no enrichment pipeline
```

---

## 🏷️ Feature Flags (so "not connected" ≠ broken)

### **❌ NOT IMPLEMENTED - Feature Flags System**

**Required Implementation:**
```python
# settings.py
FEATURE_FLAGS = {
    "properties_v1": False,  # Properties management
    "leads_crud": False,     # Leads CRUD operations
    "campaigns_v1": False,   # Campaigns system
    "analytics_events": False, # Analytics events
    "settings_v1": False,    # Settings management
    "webchat_channel": True, # Web chat (working)
    "fb_ig_channels": False, # Social media channels
    "setup_wizard": False,   # Setup wizard backend
    "auth_system": False,    # Authentication system
    "multi_tenancy": False,  # Multi-tenancy
}
```

**Template Pattern (NOT IMPLEMENTED):**
```html
<!-- NOT IMPLEMENTED -->
{% if FEATURE_FLAGS.properties_v1 %}
  <button ...>Add Property</button>
{% else %}
  <button disabled title="Coming soon—enable in staging">Add Property</button>
{% endif %}
```

---

## ✅ "Make Everything Flow" DoD per Page (use this as acceptance)

### **Dashboard**
- ❌ Tiles: Properties count + Leads count use real queries (company-scoped)
- ❌ All CTA buttons either navigate or show disabled tooltip (no dead click)
- ❌ Recent activity list pulls from Event table (last 5)

### **Properties**
- ❌ "Add Property" opens modal; create → appears in list in <1s
- ❌ Bulk actions disabled unless ≥1 row selected (with tooltip)
- ❌ Search/filter submits via HTMX to #results and preserves query params

### **Leads**
- ❌ "Assign to Agent" posts; toast on success; table row updates without refresh
- ❌ Duplicate submit within 24h blocked; UI shows reason

### **Settings**
- ❌ Save posts to /settings/save, returns ✅ toast; values persist on reload

### **Chat**
- ✅ Lead capture form validates (email/phone); rate-limited; autoresponder enqueued

---

## 🚨 CRITICAL SYSTEM ISSUES

### **1. NO MULTI-TENANCY**
- All data is global (not tenant-isolated)
- No Company model
- No company scoping in queries
- No tenant-aware middleware

### **2. NO AUTHENTICATION SYSTEM**
- Only 5 out of 58 views protected
- No user registration backend
- No login/logout backend
- No session management

### **3. NO REAL DATA MANAGEMENT**
- All internal pages use mock data
- No CRUD operations for properties, leads, campaigns
- No real analytics data
- No settings persistence

### **4. NO MODAL SYSTEM**
- No modal infrastructure
- No HTMX modal loading
- No accessibility features
- No keyboard navigation

### **5. NO FEATURE FLAGS**
- No feature flag system
- No progressive rollout
- No A/B testing capability

### **6. NO ERROR HANDLING**
- No comprehensive error handling
- No logging system
- No monitoring
- No alerting

---

## 📊 SYSTEM COMPLETION STATUS

**Overall Completion: 25%**

- **UI/UX**: 90% Complete ✅
- **Core Real Estate**: 80% Complete ✅
- **AI Integration**: 70% Complete ✅
- **Authentication**: 5% Complete ❌
- **Multi-tenancy**: 0% Complete ❌
- **Data Management**: 20% Complete ❌
- **External Integrations**: 30% Complete ❌
- **Production Readiness**: 10% Complete ❌

---

**Last Updated**: Current system analysis  
**Status**: 25% Complete (UI Complete, Backend 25% Complete)  
**Critical Issues**: 6 major system issues identified  
**Next Priority**: Implement authentication system and multi-tenancy
