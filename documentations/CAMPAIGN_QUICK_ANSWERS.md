# Campaign System - Quick Answers

## Your Questions Answered

### 1. What is the current function/supposed to be function of campaigns?

**Current State**: 
- Campaign models exist (`Campaign`, `CampaignStep`, `MessageLog`)
- Basic email service exists but uses **Postmark** (not Gmail)
- Campaign UI page exists but shows **mock data only**
- No real campaign sending implemented

**Supposed Function**:
- **Blast Campaigns**: Send one-time email to multiple leads
- **Sequence Campaigns**: Automated multi-step email follow-ups (Day 0, Day 3, Day 7, etc.)
- Track opens, clicks, bounces
- Personalize emails with lead and property data

---

### 2. Is it through n8n? What are the payloads and expectations?

**Answer**: **Yes, recommended via n8n** (but not implemented yet)

**Payload Structure** (see `N8N_CAMPAIGN_WORKFLOW_PAYLOAD.md` for details):
```json
{
  "campaign_id": "uuid",
  "organization_id": "uuid",
  "email_account": {
    "email": "sales@company.com",
    "access_token": "...",
    "refresh_token": "..."
  },
  "audience": {
    "lead_ids": ["uuid1", "uuid2"]
  },
  "template": {
    "subject": "New Properties in {{ lead.city }}",
    "body_html": "<h1>Hello {{ lead.name }}</h1>..."
  }
}
```

**n8n Workflow**:
1. Receive webhook trigger
2. Fetch leads from Django API
3. Render email templates
4. Send via Gmail API
5. Log results back to Django

---

### 3. We currently have Google OAuth right? Did we get the token?

**Answer**: **YES and NO**

✅ **YES**: Google OAuth login exists
✅ **YES**: We get `access_token` and `refresh_token`
❌ **NO**: Tokens are **NOT stored in database**
❌ **NO**: Tokens only sent via webhook (`send_gmail_sso_webhook`)
❌ **NO**: OAuth scope is wrong - only `openid email profile` (missing Gmail API scope!)

**Current Flow**:
```
Google OAuth → Get tokens → Send webhook → Tokens lost ❌
```

**What We Need**:
```
Google OAuth (with Gmail scope) → Store tokens in EmailAccount model → Use for campaigns ✅
```

---

### 4. Can we send emails on their behalf?

**Current**: **NO** ❌

**Why Not**:
1. OAuth scope doesn't include `https://www.googleapis.com/auth/gmail.send`
2. Tokens not stored, so can't reuse them
3. Current OAuth is only for login, not email sending

**What's Needed**:
1. New OAuth flow with Gmail API scope
2. Store tokens in `EmailAccount` model
3. Use stored tokens to send emails via Gmail API

---

### 5. Do we have an option to connect the email they want to use?

**Current**: **NO** ❌

There's no UI or flow for users to:
- Connect their Gmail account for campaigns
- Select which email address to use
- Manage multiple email accounts

**What's Needed**:
1. "Connect Gmail" button in Settings
2. OAuth flow with Gmail API scope
3. Store connection in `EmailAccount` model
4. UI to select primary email for campaigns

---

### 6. What's your suggestion? What's the best option?

## 🎯 Recommended Solution: **Hybrid n8n + Direct Gmail API**

### Why This Approach?

✅ **NO Redis/Celery** (as you requested - no bullshit!)
✅ **Simple**: Direct Gmail API calls
✅ **Scalable**: n8n handles orchestration
✅ **Flexible**: Easy to modify workflows
✅ **Reliable**: n8n handles retries and error handling

### Architecture

```
┌─────────────────────────────────────────┐
│          Django App                      │
│                                          │
│  1. User connects Gmail (OAuth)         │
│  2. Tokens stored in EmailAccount       │
│  3. User creates campaign               │
│  4. User selects leads                  │
│  5. Click "Send Campaign"               │
│                                          │
│  POST → n8n webhook                     │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│          n8n Workflow                    │
│                                          │
│  1. Receive webhook                      │
│  2. Fetch leads from Django API         │
│  3. Loop: Render template per lead      │
│  4. Send via Gmail API (direct)          │
│  5. Log results back to Django          │
└─────────────────────────────────────────┘
```

### Implementation Steps

#### Step 1: Add EmailAccount Model
```python
class EmailAccount(models.Model):
    organization = models.ForeignKey(Organization)
    email_address = models.EmailField()
    access_token = models.TextField()
    refresh_token = models.TextField()
    is_primary = models.BooleanField(default=False)
    # ...
```

#### Step 2: Gmail OAuth Connection
- New endpoint: `/email/connect/`
- OAuth with scope: `https://www.googleapis.com/auth/gmail.send`
- Store tokens in `EmailAccount`

#### Step 3: Campaign Send Flow
```
1. User creates campaign
2. User selects leads
3. User selects email account
4. Django → POST to n8n webhook
5. n8n sends emails via Gmail API
6. n8n → POST logs back to Django
```

#### Step 4: n8n Workflow
- Webhook trigger
- Function to fetch leads
- Loop to send emails
- Gmail API node (or HTTP Request)
- Callback to Django to log messages

---

## What to Build Next

### Priority 1: Email Connection
- [ ] `EmailAccount` model + migration
- [ ] Gmail OAuth endpoint (`/email/connect/`)
- [ ] Settings UI for "Connect Gmail"
- [ ] Token storage and refresh logic

### Priority 2: Campaign UI
- [ ] Real campaign creation form (not mock)
- [ ] Lead selection interface
- [ ] Email account selector
- [ ] Campaign preview

### Priority 3: n8n Integration
- [ ] n8n webhook endpoint in Django
- [ ] n8n workflow JSON
- [ ] Callback endpoints for logging

### Priority 4: Testing
- [ ] Test Gmail OAuth flow
- [ ] Test email sending
- [ ] Test campaign creation
- [ ] End-to-end test

---

## Alternative: Pure Direct (No n8n)

If you want even simpler (small scale):

```python
# In Django view
def send_campaign(request, campaign_id):
    campaign = Campaign.objects.get(id=campaign_id)
    email_account = EmailAccount.objects.get(organization=request.organization, is_primary=True)
    leads = Lead.objects.filter(...)
    
    for lead in leads:
        # Direct Gmail API call
        send_gmail_email(
            access_token=email_account.access_token,
            to=lead.email,
            subject=render_template(campaign.subject, {'lead': lead}),
            html=render_template(campaign.body_html, {'lead': lead})
        )
        
        # Log immediately
        MessageLog.objects.create(...)
    
    return JsonResponse({'status': 'sent'})
```

**Pros**: Simple, direct
**Cons**: No retries, no scheduling, blocks request (bad for large campaigns)

**Recommendation**: Use n8n for campaigns with > 50 leads, direct for smaller.

---

## Summary

| Question | Answer |
|----------|--------|
| Current campaign function? | Models exist, UI is mock, no real sending |
| Through n8n? | **Recommended but not implemented** |
| Payloads? | See `N8N_CAMPAIGN_WORKFLOW_PAYLOAD.md` |
| Google OAuth tokens? | **NOT stored, only sent via webhook** |
| Can send emails? | **NO - wrong scope, tokens not stored** |
| Connect email option? | **NO - doesn't exist** |
| Best solution? | **Hybrid: n8n + Direct Gmail API, NO Redis/Celery** |

---

## Next Action Items

1. **Read**: `CAMPAIGN_SYSTEM_DOCUMENTATION.md` for full details
2. **Read**: `N8N_CAMPAIGN_WORKFLOW_PAYLOAD.md` for payload specs
3. **Build**: `EmailAccount` model first
4. **Build**: Gmail OAuth connection flow
5. **Build**: n8n workflow JSON
6. **Test**: End-to-end flow

