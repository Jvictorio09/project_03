# n8n Campaign Workflow - Payload & Expectations

## Workflow Trigger: Campaign Dispatch

### Endpoint
```
POST {{ N8N_BASE_URL }}/webhook/campaign-dispatch
```

### Headers
```json
{
  "Content-Type": "application/json",
  "X-N8N-Signature": "{{ N8N_WEBHOOK_SECRET }}"
}
```

### Request Payload

#### Full Payload Structure
```json
{
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "550e8400-e29b-41d4-a716-446655440001",
  "campaign_type": "blast",
  "campaign_step_id": null,
  
  "email_account": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "email": "sales@company.com",
    "name": "John Doe",
    "access_token": "ya29.a0AfH6...",
    "refresh_token": "1//04...", 
    "expires_at": "2024-01-15T12:00:00Z"
  },
  
  "sender": {
    "email": "sales@company.com",
    "name": "John Doe",
    "reply_to": "noreply@company.com"
  },
  
  "audience": {
    "lead_ids": [
      "550e8400-e29b-41d4-a716-446655440010",
      "550e8400-e29b-41d4-a716-446655440011"
    ]
  },
  
  "template": {
    "subject": "New Properties in {{ lead.city }}",
    "body_html": "<h1>Hello {{ lead.name }}</h1><p>We have amazing properties...</p>",
    "body_text": "Hello {{ lead.name }}, We have amazing properties..."
  },
  
  "settings": {
    "send_immediately": true,
    "schedule_time": null,
    "timezone": "America/Los_Angeles",
    "track_opens": true,
    "track_clicks": true
  }
}
```

#### Sequence Campaign Payload
```json
{
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "550e8400-e29b-41d4-a716-446655440001",
  "campaign_type": "sequence",
  "campaign_step_id": "550e8400-e29b-41d4-a716-446655440003",
  
  "email_account": { /* same as above */ },
  "sender": { /* same as above */ },
  
  "audience": {
    "lead_ids": ["..."]
  },
  
  "template": {
    "subject": "Follow-up: Properties in {{ lead.city }}",
    "body_html": "...",
    "body_text": "..."
  },
  
  "settings": {
    "send_immediately": false,
    "schedule_time": "2024-01-18T10:00:00Z",
    "offset_days": 3
  }
}
```

---

## n8n Workflow Steps

### Step 1: Webhook Trigger
- **Node Type**: Webhook
- **Method**: POST
- **Path**: `/webhook/campaign-dispatch`
- **Response**: `{ "status": "received", "execution_id": "..." }`

### Step 2: Function - Validate & Extract
```javascript
const payload = $json;

// Validate required fields
if (!payload.campaign_id || !payload.organization_id || !payload.email_account) {
  throw new Error('Missing required fields');
}

return {
  campaign_id: payload.campaign_id,
  organization_id: payload.organization_id,
  campaign_type: payload.campaign_type,
  email_account: payload.email_account,
  sender: payload.sender,
  audience: payload.audience,
  template: payload.template,
  settings: payload.settings
};
```

### Step 3: HTTP Request - Fetch Leads
```
GET {{ DJANGO_BASE_URL }}/api/leads/bulk/
Headers: {
  "Authorization": "Bearer {{ N8N_TOKEN }}",
  "Content-Type": "application/json"
}
Body: {
  "organization_id": "{{ $json.organization_id }}",
  "lead_ids": {{ $json.audience.lead_ids }}
}
```

**Response**:
```json
{
  "leads": [
    {
      "id": "uuid",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "city": "Los Angeles",
      "budget_max": 800000,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Step 4: Split in Batches
- **Node Type**: Split in Batches
- **Batch Size**: 10 (to avoid rate limits)

### Step 5: Loop - Process Each Lead
- **Node Type**: Loop Over Items

### Step 6: Function - Render Template
```javascript
const lead = $json.lead;
const template = $json.template;

// Simple template rendering
const renderTemplate = (template, data) => {
  let result = template;
  
  // Replace {{ lead.name }}, {{ lead.email }}, etc.
  Object.keys(data).forEach(key => {
    if (typeof data[key] === 'object' && data[key] !== null) {
      Object.keys(data[key]).forEach(subKey => {
        const pattern = new RegExp(`\\{\\{\\s*${key}\\.${subKey}\\s*\\}\\}`, 'g');
        result = result.replace(pattern, data[key][subKey] || '');
      });
    } else {
      const pattern = new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g');
      result = result.replace(pattern, data[key] || '');
    }
  });
  
  return result;
};

const subject = renderTemplate(template.subject, { lead });
const body_html = renderTemplate(template.body_html, { lead });
const body_text = renderTemplate(template.body_text, { lead });

return {
  lead_id: lead.id,
  to: lead.email,
  subject,
  body_html,
  body_text
};
```

### Step 7: Gmail API - Send Email
```
POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send
Headers: {
  "Authorization": "Bearer {{ $json.email_account.access_token }}",
  "Content-Type": "application/json"
}
Body: {
  "raw": "{{ base64Encode(emailMessage) }}"
}
```

**Email Message Format** (before base64):
```
From: {{ $json.sender.name }} <{{ $json.sender.email }}>
To: {{ $json.to }}
Subject: {{ $json.subject }}
Content-Type: text/html; charset=utf-8

{{ $json.body_html }}
```

### Step 8: HTTP Request - Log Message
```
POST {{ DJANGO_BASE_URL }}/api/campaigns/log-message/
Headers: {
  "Authorization": "Bearer {{ N8N_TOKEN }}",
  "Content-Type": "application/json"
}
Body: {
  "campaign_id": "{{ $json.campaign_id }}",
  "lead_id": "{{ $json.lead_id }}",
  "campaign_step_id": "{{ $json.campaign_step_id }}",
  "status": "sent",
  "provider_message_id": "{{ $json.gmail_response.id }}",
  "sent_at": "{{ $now }}"
}
```

### Step 9: Aggregate Results
- **Node Type**: Aggregate
- **Operation**: Collect all results

### Step 10: HTTP Request - Update Campaign Status
```
POST {{ DJANGO_BASE_URL }}/api/campaigns/status/
Headers: {
  "Authorization": "Bearer {{ N8N_TOKEN }}",
  "Content-Type": "application/json"
}
Body: {
  "campaign_id": "{{ $json.campaign_id }}",
  "status": "completed",
  "stats": {
    "total_leads": {{ $json.total }},
    "sent": {{ $json.sent_count }},
    "failed": {{ $json.failed_count }},
    "delivery_rate": {{ $json.sent_count / $json.total * 100 }}
  },
  "errors": {{ $json.errors }}
}
```

---

## Callback Endpoints (Django)

### 1. Log Message
```
POST /api/campaigns/log-message/
Authorization: Bearer {{ N8N_TOKEN }}
```

**Payload**:
```json
{
  "campaign_id": "uuid",
  "lead_id": "uuid",
  "campaign_step_id": "uuid",
  "status": "sent",
  "provider_message_id": "gmail_message_id",
  "sent_at": "2024-01-15T10:00:00Z"
}
```

### 2. Update Campaign Status
```
POST /api/campaigns/status/
Authorization: Bearer {{ N8N_TOKEN }}
```

**Payload**:
```json
{
  "campaign_id": "uuid",
  "status": "completed",
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

---

## Error Handling

### Token Expiry
If `access_token` is expired:
1. Use `refresh_token` to get new access token
2. Update `email_account` in database
3. Retry email send

### Rate Limiting
- Gmail API: 250 emails/day (free tier) or 2000/day (workspace)
- Split into batches with delays
- Track rate limit in n8n variables

### Failed Emails
- Log as `status='failed'` in MessageLog
- Include error message
- Continue with next email (don't stop workflow)

---

## Testing

### Test Payload
```json
{
  "campaign_id": "test-uuid",
  "organization_id": "test-org-uuid",
  "campaign_type": "blast",
  "email_account": {
    "email": "test@example.com",
    "access_token": "test-token"
  },
  "sender": {
    "email": "test@example.com",
    "name": "Test Sender"
  },
  "audience": {
    "lead_ids": ["test-lead-uuid"]
  },
  "template": {
    "subject": "Test Email",
    "body_html": "<p>Test</p>",
    "body_text": "Test"
  },
  "settings": {
    "send_immediately": true
  }
}
```

---

## Security Notes

1. **Access Tokens**: Should be encrypted in database
2. **Webhook Secret**: Validate signature on Django side
3. **N8N_TOKEN**: Store in n8n environment variables
4. **HTTPS Only**: All endpoints must use HTTPS

