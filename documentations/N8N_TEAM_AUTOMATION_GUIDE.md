# N8N Automation Implementation Guide for n8n Team

This document outlines all automation workflows that need to be implemented in n8n for the Property Management Platform.

---

## 1. Facebook/Meta Authentication & Connection Automation

### Purpose
Automate the Facebook page connection process so organizations can connect their Facebook pages and enable automated messaging.

### Flow Overview
```
User initiates connection → n8n handles Facebook OAuth → Store credentials → Subscribe to webhooks
```

### Required Workflow

#### Step 1: Facebook OAuth Initiation
**Endpoint**: Custom Webhook (triggered from Django)
**Payload**:
```json
{
  "organization_id": "uuid",
  "redirect_url": "https://app.example.com/settings",
  "action": "connect_facebook"
}
```

**n8n Actions**:
1. Generate Facebook OAuth URL with:
   - App ID from environment variables
   - Required scopes: `pages_messaging`, `pages_read_user_content`, `pages_manage_metadata`
   - Redirect URI pointing back to Django callback
   - State parameter (organization_id)
2. Return OAuth URL to Django

#### Step 2: Handle OAuth Callback
**Endpoint**: Custom Webhook (called by Facebook after user authorizes)
**Payload** (from Facebook):
```json
{
  "code": "facebook_auth_code",
  "state": "organization_id",
  "redirect_uri": "https://app.example.com/callback"
}
```

**n8n Actions**:
1. Exchange authorization code for access token
   - POST to `https://graph.facebook.com/v18.0/oauth/access_token`
   - Parameters: `client_id`, `client_secret`, `redirect_uri`, `code`
2. Get user's pages
   - GET `https://graph.facebook.com/v18.0/me/accounts?access_token={token}`
3. For selected page, get page access token
   - GET `https://graph.facebook.com/v18.0/{page_id}?fields=access_token,name,id&access_token={token}`
4. Subscribe page to webhooks
   - POST `https://graph.facebook.com/v18.0/{page_id}/subscribed_apps`
   - Body: `subscribed_fields=messages,messaging_postbacks,messaging_optins`
   - Use page access token
5. Call Django callback endpoint:
   - POST `{{ DJANGO_BASE_URL }}/api/facebook/connection-complete/`
   - Headers: `Authorization: Bearer {{ N8N_TOKEN }}`
   - Body:
     ```json
     {
       "organization_id": "{{ state }}",
       "page_id": "{{ page_id }}",
       "page_name": "{{ page_name }}",
       "page_access_token": "{{ page_access_token }}",
       "connected_at": "{{ timestamp }}"
     }
     ```

### Required Environment Variables
- `FACEBOOK_APP_ID`
- `FACEBOOK_APP_SECRET`
- `DJANGO_BASE_URL`
- `N8N_TOKEN`

---

## 2. AI Property Response Automation (Facebook/Instagram Messaging)

### Purpose
When someone messages the Facebook/Instagram page, AI should respond using property data from the system to answer questions intelligently.

### Flow Overview
```
Facebook Webhook → n8n → Get properties from Django → AI generates response → Send reply to Facebook
```

### Required Workflow

#### Step 1: Receive Facebook Webhook
**Endpoint**: Webhook (configured in Facebook Developer Console)
**Facebook Webhook Payload**:
```json
{
  "object": "page",
  "entry": [{
    "id": "page_id",
    "messaging": [{
      "sender": { "id": "user_id" },
      "recipient": { "id": "page_id" },
      "message": {
        "text": "Looking for 2BR condo in BGC under 5M"
      },
      "timestamp": 1234567890
    }]
  }]
}
```

**n8n Actions**:
1. Verify webhook signature (Meta signature verification)
2. Extract message text and sender ID
3. Find organization by page_id (call Django API)
   - GET `{{ DJANGO_BASE_URL }}/api/organizations/by-facebook-page/{{ page_id }}/`
   - Headers: `Authorization: Bearer {{ N8N_TOKEN }}`
4. Get property knowledge base from Django
   - GET `{{ DJANGO_BASE_URL }}/api/organizations/{{ organization_id }}/properties/`
   - Query params: `format=knowledge_base`
   - This returns all properties with details formatted for AI context

#### Step 2: Prepare AI Context
**n8n Actions**:
1. Format properties for AI context:
   ```javascript
   // Code Node
   const properties = $json.body.properties || [];
   const knowledgeBase = properties.map(p => ({
     title: p.title,
     price: p.price_amount,
     beds: p.beds,
     baths: p.baths,
     city: p.city,
     area: p.area,
     description: p.description,
     features: p.property_features || [],
     amenities: p.nearby_amenities || []
   }));
   
   return {
     message: $prevNode('Extract Message').item.json.message.text,
     sender_id: $prevNode('Extract Message').item.json.sender.id,
     organization_id: $prevNode('Find Organization').item.json.body.organization_id,
     properties: knowledgeBase
   };
   ```

#### Step 3: Generate AI Response
**n8n Actions**:
1. Call OpenAI API with:
   - **System Prompt**:
     ```
     You are a helpful real estate assistant for {{ organization_name }}. 
     You have access to the following properties. Answer questions about these properties 
     accurately and helpfully. If asked about properties matching certain criteria, 
     provide relevant options from the available properties. Always be professional 
     and encourage scheduling viewings for interested leads.
     ```
   - **User Message**: Format with user's question and property data
   - **Model**: `gpt-4o-mini` or `gpt-4`
   - **Temperature**: 0.7
   - **Max Tokens**: 500

#### Step 4: Send Response to Facebook
**n8n Actions**:
1. Get page access token from organization
   - Already stored from connection flow
2. Send message via Facebook Graph API:
   - POST `https://graph.facebook.com/v18.0/me/messages`
   - Query params: `access_token={{ page_access_token }}`
   - Body:
     ```json
     {
       "recipient": { "id": "{{ sender_id }}" },
       "message": { "text": "{{ ai_response }}" },
       "messaging_type": "RESPONSE"
     }
     ```

#### Step 5: Notify Django
**n8n Actions**:
1. POST to Django to log the conversation:
   - POST `{{ DJANGO_BASE_URL }}/api/channel-messages/`
   - Body:
     ```json
     {
       "organization_id": "{{ organization_id }}",
       "channel": "facebook",
       "sender_id": "{{ sender_id }}",
       "message_text": "{{ original_message }}",
       "response_text": "{{ ai_response }}",
       "timestamp": "{{ timestamp }}"
     }
     ```

### Required Environment Variables
- `DJANGO_BASE_URL`
- `N8N_TOKEN`
- `OPENAI_API_KEY`
- `FACEBOOK_VERIFY_TOKEN` (for webhook verification)

### Webhook Configuration in Facebook Developer Console
- **Webhook URL**: `https://your-n8n-instance.com/webhook/facebook-messenger`
- **Verify Token**: Value from `FACEBOOK_VERIFY_TOKEN` env var
- **Subscription Fields**: `messages`, `messaging_postbacks`, `messaging_optins`

---

## 3. Email Automation with Property Knowledge

### Purpose
Automatically send personalized emails to leads using property data from the system. The AI uses property knowledge to recommend relevant properties and answer questions.

### Flow Overview
```
Lead created/updated → n8n triggered → Get properties from Django → AI generates email → Send via email service
```

### Required Workflows

#### Workflow A: Lead Welcome Email Sequence

**Trigger**: Webhook from Django
**Payload**:
```json
{
  "lead_id": "uuid",
  "organization_id": "uuid",
  "lead_data": {
    "name": "Maria Santos",
    "email": "maria@example.com",
    "budget_max": 5000000,
    "beds": 2,
    "areas": "BGC, Makati",
    "buy_or_rent": "buy"
  },
  "trigger": "lead_created",
  "sequence_type": "welcome"
}
```

**n8n Actions**:
1. Get matching properties from Django
   - GET `{{ DJANGO_BASE_URL }}/api/organizations/{{ organization_id }}/properties/?beds={{ beds }}&city={{ areas }}&price_max={{ budget_max }}`
   - Headers: `Authorization: Bearer {{ N8N_TOKEN }}`

2. Format properties for email context
   ```javascript
   // Code Node
   const properties = $json.body.properties.slice(0, 5); // Top 5 matches
   return {
     lead: $prevNode('Receive Trigger').item.json.lead_data,
     properties: properties.map(p => ({
       title: p.title,
       price: `₱${p.price_amount.toLocaleString()}`,
       beds: p.beds,
       baths: p.baths,
       location: `${p.city}, ${p.area}`,
       description: p.description,
       slug: p.slug,
       url: `https://app.example.com/property/${p.slug}`
     })),
     organization_name: $json.body.organization_name
   };
   ```

3. Generate email content with AI
   - **System Prompt**:
     ```
     You are writing a welcome email for a real estate lead. The lead is interested in 
     {{ property_type }} properties in {{ areas }} with a budget of {{ budget_max }}.
     You have {{ property_count }} properties to recommend. Write a friendly, 
     professional email that welcomes them and highlights 3-5 most relevant properties.
     Include property details naturally in the email. End with a call-to-action to 
     schedule a viewing.
     ```
   - **User Message**: Include lead preferences and property list
   - **Model**: `gpt-4o-mini`
   - **Temperature**: 0.7

4. Send email via Resend API
   - POST `https://api.resend.com/emails`
   - Headers:
     - `Authorization: Bearer {{ RESEND_API_KEY }}`
     - `Content-Type: application/json`
   - Body:
     ```json
     {
       "from": "{{ organization_name }} <noreply@katek.ai>",
       "to": ["{{ lead_email }}"],
       "subject": "Welcome! Properties You Might Love",
       "html": "{{ ai_email_content }}"
     }
     ```

5. Call Django callback
   - POST `{{ DJANGO_BASE_URL }}/api/email-sent/`
   - Body:
     ```json
     {
       "lead_id": "{{ lead_id }}",
       "email_type": "welcome",
       "status": "sent",
       "provider_message_id": "{{ resend_message_id }}"
     }
     ```

#### Workflow B: Property Update Email (New Listings)

**Trigger**: Webhook from Django when new properties are added
**Payload**:
```json
{
  "organization_id": "uuid",
  "property_id": "uuid",
  "property_data": {
    "title": "Luxury 2BR in BGC",
    "price_amount": 4500000,
    "beds": 2,
    "city": "Taguig",
    "area": "BGC"
  },
  "target_leads": ["lead_uuid_1", "lead_uuid_2"]
}
```

**n8n Actions**:
1. Get target leads data
   - POST `{{ DJANGO_BASE_URL }}/api/leads/batch/`
   - Body: `{ "lead_ids": ["lead_uuid_1", "lead_uuid_2"] }`
   - Returns lead preferences

2. For each lead, generate personalized email
   ```javascript
   // Code Node
   const lead = $json.body;
   const property = $prevNode('Receive Trigger').item.json.property_data;
   
   // Match property to lead preferences
   const isGoodMatch = 
     (lead.budget_max >= property.price_amount) &&
     (lead.beds <= property.beds || lead.beds === null) &&
     (lead.areas.includes(property.city) || lead.areas === null);
   
   if (!isGoodMatch) return null; // Skip if no match
   
   return {
     lead: lead,
     property: property,
     match_reason: "Fits your budget and location preferences"
   };
   ```

3. Generate AI email for matched leads
   - **System Prompt**:
     ```
     Write a short, exciting email about a new property listing. The property matches 
     the lead's preferences ({{ match_reason }}). Be enthusiastic but professional. 
     Highlight key features and include a clear call-to-action.
     ```
   - **Model**: `gpt-4o-mini`
   - **Max Tokens**: 300

4. Send email batch via Resend
   - Use Resend batch API or loop through leads

#### Workflow C: Follow-up Email Sequence

**Trigger**: Schedule (daily cron) or webhook based on lead age
**Payload** (from Django API):
```json
{
  "lead_id": "uuid",
  "organization_id": "uuid",
  "days_since_creation": 7,
  "lead_data": { ... },
  "last_interaction": "2024-01-10",
  "properties_viewed": ["prop_1", "prop_2"]
}
```

**n8n Actions**:
1. Get updated property recommendations
   - GET `{{ DJANGO_BASE_URL }}/api/leads/{{ lead_id }}/recommended-properties/`

2. Generate follow-up email with AI
   - Use lead engagement history to personalize
   - Include newly listed properties
   - Reference previously viewed properties

3. Send via Resend

4. Log to Django

### Required Environment Variables
- `DJANGO_BASE_URL`
- `N8N_TOKEN`
- `RESEND_API_KEY`
- `OPENAI_API_KEY`

### Django API Endpoints Reference

#### Get Properties (Knowledge Base)
```
GET {{ DJANGO_BASE_URL }}/api/organizations/{org_id}/properties/
Headers: Authorization: Bearer {{ N8N_TOKEN }}
Query Params:
  - beds (optional)
  - city (optional)
  - price_max (optional)
  - format=knowledge_base (for AI context)
```

#### Get Organization by Facebook Page
```
GET {{ DJANGO_BASE_URL }}/api/organizations/by-facebook-page/{page_id}/
Headers: Authorization: Bearer {{ N8N_TOKEN }}
```

#### Log Channel Message
```
POST {{ DJANGO_BASE_URL }}/api/channel-messages/
Headers: Authorization: Bearer {{ N8N_TOKEN }}
Body: {
  "organization_id": "uuid",
  "channel": "facebook|instagram|email",
  "sender_id": "string",
  "message_text": "string",
  "response_text": "string"
}
```

#### Email Sent Callback
```
POST {{ DJANGO_BASE_URL }}/api/email-sent/
Headers: Authorization: Bearer {{ N8N_TOKEN }}
Body: {
  "lead_id": "uuid",
  "email_type": "welcome|followup|property_update",
  "status": "sent|failed",
  "provider_message_id": "string"
}
```

---

## Authentication & Security

### All n8n → Django Calls
- **Method**: POST/GET with Bearer token
- **Header**: `Authorization: Bearer {{ N8N_TOKEN }}`
- **Content-Type**: `application/json`

### Webhook Verification (Facebook)
```javascript
// Code Node for Facebook webhook verification
const crypto = require('crypto');
const verifyToken = process.env.FACEBOOK_VERIFY_TOKEN;
const hubVerifyToken = $query.hub.verify_token;

if (hubVerifyToken === verifyToken) {
  return { challenge: $query.hub.challenge };
} else {
  return { error: 'Verification failed' };
}
```

### HMAC Signature (Django Callbacks)
For secure Django callbacks, n8n should:
1. Create timestamp
2. Create payload JSON string
3. Sign: `HMAC-SHA256(timestamp + "." + payload, secret)`
4. Send headers:
   - `X-Signature: sha256={signature}`
   - `X-Timestamp: {timestamp}`

---

## Implementation Priority

1. **Phase 1** (Week 1):
   - Facebook OAuth connection flow
   - Basic Facebook webhook handler
   - Simple AI response (without property matching)

2. **Phase 2** (Week 2):
   - Property knowledge base integration
   - AI property matching and recommendations
   - Welcome email automation

3. **Phase 3** (Week 3):
   - Follow-up email sequences
   - Property update emails
   - Advanced AI personalization

---

## Testing Checklist

- [ ] Facebook OAuth flow completes successfully
- [ ] Facebook webhook receives and processes messages
- [ ] Property data retrieved correctly from Django
- [ ] AI generates relevant responses using property data
- [ ] Facebook replies sent successfully
- [ ] Email automation sends welcome emails
- [ ] Email automation uses correct property data
- [ ] Email automation personalizes content with AI
- [ ] All Django callbacks working
- [ ] Error handling for API failures
- [ ] Webhook signature verification working

---

## Support & Documentation

- **Django API Documentation**: `documentations/API_CONTRACTS_DASHBOARD.md`
- **Architecture Overview**: `documentations/architecture/N8N_INTEGRATION_ARCHITECTURE.md`
- **Existing Workflows**: `n8n_json/` directory

