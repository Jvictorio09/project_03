# Campaign System Documentation

## Table of Contents
1. [Current Implementation Status](#current-implementation-status)
2. [Campaign Functionality Overview](#campaign-functionality-overview)
3. [Google OAuth & Email Connection](#google-oauth--email-connection)
4. [n8n Integration Architecture](#n8n-integration-architecture)
5. [Recommended Solution](#recommended-solution)
6. [Implementation Guide](#implementation-guide)

---

## Current Implementation Status

### ✅ What Exists
- **Campaign Models**: `Campaign`, `CampaignStep`, `MessageLog` models fully defined
- **Email Service**: `EmailCampaignService` in `services_email.py` using Postmark
- **Campaign View**: Basic `/campaigns/` page (currently shows mock data)
- **Google OAuth**: Login flow exists, BUT:
  - ⚠️ **Tokens NOT stored in database**
  - ⚠️ **Only sent via webhook** (`send_gmail_sso_webhook`)
  - ⚠️ **Scope is limited**: `openid email profile` (NOT Gmail API)

### ❌ What's Missing
1. **Gmail API OAuth**: Need `https://www.googleapis.com/auth/gmail.send` scope
2. **Token Storage**: No model to store OAuth tokens per organization/user
3. **Email Connection UI**: No way for users to connect their Gmail account
4. **Campaign Creation UI**: Campaign page only shows mocks
5. **Real Campaign Sending**: Service exists but not wired up

---

## Campaign Functionality Overview

### Campaign Types

#### 1. **Blast Campaign** (`type='blast'`)
- Send one-time email to multiple leads
- Immediate delivery
- Single email template

#### 2. **Sequence Campaign** (`type='sequence'`)
- Multi-step email automation
- Time-based triggers (`offset_days`)
- Example: Day 0 welcome, Day 3 follow-up, Day 7 offer

### Campaign Model Fields
```python
- id (UUID)
- organization (FK)
- name (string)
- type ('blast' | 'sequence')
- status ('draft' | 'active' | 'paused' | 'completed')
- created_at, updated_at
```

### CampaignStep Model (for sequences)
```python
- id (UUID)
- campaign (FK)
- offset_days (int)  # Days after lead creation
- subject (string)
- body_template (text)  # Jinja template
- order (int)
```

### MessageLog Model (tracking)
```python
- id (UUID)
- organization (FK)
- campaign (FK)
- campaign_step (FK, nullable)
- lead (FK)
- status ('sent' | 'delivered' | 'opened' | 'clicked' | 'bounced' | 'failed')
- provider_message_id (string)
- opened_at, clicked_at (datetime)
- error_message (text)
```

---

## Google OAuth & Email Connection

### Current OAuth Implementation

**File**: `myApp/views_google_oauth.py`

**Current Flow**:
```python
1. User clicks "Login with Google"
2. Redirected to Google OAuth
3. Callback receives access_token + refresh_token
4. Tokens sent via webhook: send_gmail_sso_webhook()
5. Tokens NOT stored in database ❌
```

**Current Scope**:
```
scope=openid email profile
```
**Problem**: This scope does NOT allow sending emails via Gmail API!

### Required Changes for Email Campaigns

#### 1. **Add Gmail API Scope**
```python
scope=openid email profile https://www.googleapis.com/auth/gmail.send
```

#### 2. **Create Token Storage Model**
```python
class EmailAccount(models.Model):
    """Stores OAuth tokens for email sending"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Email info
    email_address = models.EmailField()
    display_name = models.CharField(max_length=255)  # "John Doe" or "Company Name"
    
    # OAuth tokens
    access_token = models.TextField()  # Encrypted in production
    refresh_token = models.TextField()  # Encrypted in production
    token_expires_at = models.DateTimeField()
    
    # Provider
    provider = models.CharField(max_length=20, default='gmail')  # 'gmail' | 'postmark' | 'sendgrid'
    
    # Status
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)  # Primary sender for org
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 3. **Email Connection Flow**
```
1. User clicks "Connect Gmail" in Settings
2. OAuth flow with Gmail API scope
3. Store tokens in EmailAccount model
4. User selects which email to use for campaigns
```

---

## n8n Integration Architecture

### Recommended: Hybrid Approach
- **Direct**: Simple email sends (single API call)
- **n8n**: Campaign orchestration, scheduling, analytics, retries

### Option 1: Pure n8n (Recommended for Complexity)

#### Trigger: Campaign Dispatch
```
POST {{ N8N_BASE_URL }}/webhook/campaign-dispatch
```

**Payload**:
```json
{
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "550e8400-e29b-41d4-a716-446655440001",
  "campaign_type": "blast",
  "email_account_id": "550e8400-e29b-41d4-a716-446655440002",
  
  "sender": {
    "email": "sales@company.com",
    "name": "John Doe",
    "reply_to": "noreply@company.com"
  },
  
  "audience": {
    "lead_ids": ["uuid1", "uuid2"],  // OR
    "filter": {
      "status": ["new", "contacted"],
      "city": "Los Angeles",
      "budget_min": 500000
    }
  },
  
  "template": {
    "subject": "New Properties in {{ lead.city }}",
    "body_html": "<h1>Hello {{ lead.name }}</h1>...",
    "body_text": "Hello {{ lead.name }}..."
  },
  
  "campaign_step_id": "550e8400-e29b-41d4-a716-446655440003",  // For sequences
  
  "settings": {
    "send_immediately": true,
    "schedule_time": "2024-01-15T10:00:00Z",  // Optional
    "timezone": "America/Los_Angeles"
  }
}
```

#### n8n Workflow Steps

**Node 1: HTTP Request (Trigger)**
- Receives campaign dispatch payload

**Node 2: Function - Fetch Leads**
```javascript
// Query Django API or database directly
const leadIds = $json.audience.lead_ids || [];
const filter = $json.audience.filter || {};

// If lead_ids provided, use them
if (leadIds.length > 0) {
  return { leads: leadIds.map(id => ({ id })) };
}

// Otherwise build filter query
const query = {
  organization_id: $json.organization_id,
  ...filter
};

// Call Django API: GET /api/leads/?organization_id=...&status=new
```

**Node 3: Loop - Process Each Lead**
- Split items

**Node 4: Function - Render Template**
```javascript
const template = $json.template;
const lead = $json.lead;
const property = $json.property;  // If linked

const subject = template.subject
  .replace(/\{\{ lead\.name \}\}/g, lead.name)
  .replace(/\{\{ lead\.city \}\}/g, lead.city || '');

const html = template.body_html
  .replace(/\{\{ lead\.name \}\}/g, lead.name)
  .replace(/\{\{ property\.title \}\}/g, property?.title || '');

return {
  subject,
  html,
  text: template.body_text.replace(/\{\{ lead\.name \}\}/g, lead.name)
};
```

**Node 5: Gmail API - Send Email**
```javascript
// Use stored OAuth credentials from n8n credential store
// Or pass token from payload:
const emailAccount = $json.email_account;
const accessToken = emailAccount.access_token;

// Send via Gmail API
POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send
Headers: {
  "Authorization": "Bearer " + accessToken,
  "Content-Type": "application/json"
}
Body: {
  raw: base64Encode(emailMessage)
}
```

**Node 6: HTTP Request - Log to Django**
```
POST {{ DJANGO_BASE_URL }}/api/campaigns/log-message/
Authorization: Bearer {{ N8N_TOKEN }}

Payload:
{
  "campaign_id": "...",
  "lead_id": "...",
  "status": "sent",
  "provider_message_id": "...",
  "sent_at": "2024-01-15T10:00:00Z"
}
```

#### Callback: Campaign Status Update
```
POST {{ DJANGO_BASE_URL }}/api/campaigns/status/
```

**Payload**:
```json
{
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",  // "processing" | "completed" | "failed"
  "stats": {
    "total_leads": 150,
    "sent": 148,
    "failed": 2,
    "delivery_rate": 98.67
  },
  "errors": [
    {
      "lead_id": "uuid",
      "error": "Invalid email address"
    }
  ]
}
```

### Option 2: Direct Django (Simple Cases)

**Use Case**: Small blasts (< 100 emails), immediate send

**Implementation**:
```python
# In views.py or service
def send_campaign_direct(campaign_id):
    campaign = Campaign.objects.get(id=campaign_id)
    email_account = EmailAccount.objects.get(organization=campaign.organization, is_primary=True)
    
    leads = Lead.objects.filter(organization=campaign.organization, status__in=['new', 'contacted'])
    
    for lead in leads:
        # Use Gmail API directly
        send_gmail_email(
            access_token=email_account.access_token,
            to=lead.email,
            subject=campaign.steps.first().subject,
            html_body=render_template(campaign.steps.first().body_template, {'lead': lead})
        )
        
        # Log immediately
        MessageLog.objects.create(...)
```

---

## Recommended Solution

### 🎯 Best Approach: Hybrid n8n + Direct

**Why**:
- ✅ No Redis/Celery complexity (as requested)
- ✅ n8n handles orchestration, retries, scheduling
- ✅ Direct Gmail API for simplicity
- ✅ Easy to scale without background workers

### Architecture

```
┌─────────────────┐
│  Django App     │
│                 │
│  1. Create      │──────────┐
│     Campaign    │          │
│                 │          │
│  2. Select      │          │
│     Leads       │          │
│                 │          │
│  3. Choose      │          │
│     Email       │          │
│     Account     │          │
│                 │          │
│  4. Trigger     │──────────┼──► POST /webhook/campaign-dispatch
└─────────────────┘          │   (n8n)
                               │
                               ▼
                    ┌──────────────────┐
                    │   n8n Workflow   │
                    │                   │
                    │  1. Fetch Leads   │
                    │  2. Loop & Render │
                    │  3. Send Gmail    │
                    │  4. Log Results   │
                    └──────────────────┘
                               │
                               │ Callback
                               ▼
                    ┌──────────────────┐
                    │  Django API      │
                    │  /api/campaigns/ │
                    │  log-message/    │
                    └──────────────────┘
```

### Email Connection Flow

1. **User clicks "Connect Email" in Settings**
2. **OAuth with Gmail API scope**:
   ```
   scope=openid email profile https://www.googleapis.com/auth/gmail.send
   ```
3. **Store tokens** in `EmailAccount` model
4. **Test email** sent to verify connection
5. **User selects** which email to use for campaigns

---

## Implementation Guide

### Step 1: Add EmailAccount Model

```python
# myApp/models.py
class EmailAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email_address = models.EmailField()
    display_name = models.CharField(max_length=255)
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expires_at = models.DateTimeField()
    provider = models.CharField(max_length=20, default='gmail')
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Step 2: Create Gmail OAuth Endpoint

```python
# myApp/views_email_oauth.py
def connect_gmail(request):
    """Connect Gmail for email campaigns"""
    state = secrets.token_urlsafe(32)
    request.session['email_oauth_state'] = state
    request.session['email_oauth_org_id'] = str(request.organization.id)
    
    redirect_uri = request.build_absolute_uri('/email/oauth/callback/')
    
    google_oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid email profile https://www.googleapis.com/auth/gmail.send&"
        f"response_type=code&"
        f"state={state}&"
        f"access_type=offline&"  # Get refresh token
        f"prompt=consent"  # Force consent screen for refresh token
    )
    
    return redirect(google_oauth_url)

def email_oauth_callback(request):
    """Handle Gmail OAuth callback"""
    # Exchange code for tokens
    # Store in EmailAccount model
    # Test email send
    # Redirect to settings with success message
```

### Step 3: n8n Webhook Endpoint

```python
# myApp/views_webhook.py
@csrf_exempt
@require_POST
def n8n_campaign_dispatch(request):
    """Receive campaign dispatch requests from n8n"""
    data = json.loads(request.body)
    
    # Validate n8n webhook secret
    if request.headers.get('X-N8N-Signature') != settings.N8N_WEBHOOK_SECRET:
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    campaign_id = data.get('campaign_id')
    # ... validate and process
    
    return JsonResponse({'status': 'received'})
```

### Step 4: Campaign Send View

```python
# myApp/views.py
def send_campaign(request, campaign_id):
    """Trigger campaign send via n8n"""
    campaign = Campaign.objects.get(id=campaign_id, organization=request.organization)
    
    # Get primary email account
    email_account = EmailAccount.objects.get(
        organization=request.organization,
        is_primary=True,
        is_active=True
    )
    
    # Get audience
    lead_ids = request.POST.getlist('lead_ids')  # From frontend selection
    
    # Build payload
    payload = {
        "campaign_id": str(campaign.id),
        "organization_id": str(request.organization.id),
        "campaign_type": campaign.type,
        "email_account_id": str(email_account.id),
        "sender": {
            "email": email_account.email_address,
            "name": email_account.display_name
        },
        "audience": {
            "lead_ids": lead_ids
        },
        "template": {
            "subject": campaign.steps.first().subject,
            "body_html": campaign.steps.first().body_template,
            "body_text": "..."
        }
    }
    
    # Send to n8n
    response = requests.post(
        f"{settings.N8N_BASE_URL}/webhook/campaign-dispatch",
        json=payload,
        headers={"X-N8N-Signature": settings.N8N_WEBHOOK_SECRET}
    )
    
    return JsonResponse({"status": "sent", "workflow_id": response.json().get('execution_id')})
```

---

## Summary

### Current State
- ✅ Campaign models ready
- ✅ Basic email service exists
- ⚠️ No Gmail OAuth connection
- ⚠️ Tokens not stored
- ⚠️ Campaign UI is mock

### What to Build
1. **EmailAccount model** - Store OAuth tokens
2. **Gmail connection flow** - OAuth with Gmail API scope
3. **Campaign creation UI** - Real forms, not mocks
4. **n8n workflow** - Campaign dispatch automation
5. **Direct Gmail API** - Simple send, no Postmark needed

### Recommendation
**Use n8n for orchestration, direct Gmail API for sending. No Redis/Celery needed.**

---

## Next Steps

1. Create migration for `EmailAccount` model
2. Implement Gmail OAuth connection flow
3. Build campaign creation/edit UI
4. Create n8n workflow JSON
5. Add webhook endpoints for n8n callbacks
6. Test end-to-end flow

