# Automation System - Complete Guide

## 🎯 Overview

You're absolutely right! Here's how the automation system works:

### **The Flow:**

1. **Customer sends message** → Facebook Messenger / Instagram / Website Chat
2. **AI responds** → Uses your organization's persona and property data
3. **Lead captured** → Automatically stored in your CRM
4. **Webhooks sent** → To n8n/HubSpot for further processing
5. **Email automation** → Follow-up sequences sent automatically
6. **All data synced** → Everything stored in your database

---

## ✅ What We've Built

### 1. **Email Automation System** ✅

**How it works:**
- When a lead is created → Automatically sends welcome email
- Email sequences → Sends follow-up emails on Day 0, 3, 7, 14
- Campaigns → Blast emails to multiple leads
- Tracking → Opens, clicks, bounces all tracked

**Background Processing:**
- Celery task runs daily to process email sequences
- Command: `python manage.py run_automations --task email`

**API Endpoints:**
- Create campaign: `/campaigns/`
- Send campaign: `/campaigns/<id>/send`
- View stats: `/campaigns/<id>/stats`

### 2. **Facebook Messenger Integration** ✅

**How it works:**
- Connect your Facebook page → OAuth flow
- Messages come in → Webhook receives them
- AI responds → Uses your organization's persona
- Lead created → Automatically captured
- Data synced → Stored in your database

**Setup Steps:**
1. Go to Facebook Developer Console
2. Create App → Get App ID & Secret
3. Add Messenger product
4. Configure webhook URL: `https://yourdomain.com/webhook/facebook/`
5. In your dashboard → Connect Facebook page

**Webhook Endpoint:**
- `/webhook/facebook/` → Receives messages from Facebook
- `/api/connect/facebook/` → Connects page from frontend

**Data Flow:**
```
Facebook User → Facebook → Webhook → AI Chat → Lead Created → CRM Sync
```

### 3. **Instagram Direct Message Integration** ✅

**How it works:**
- Connect Instagram Business Account → OAuth flow
- Messages come in → Webhook receives them
- AI responds → Same persona as Facebook
- Lead created → Automatically captured
- Data synced → Stored in your database

**Setup Steps:**
1. Connect through Facebook (Instagram uses Facebook's API)
2. Configure webhook URL: `https://yourdomain.com/webhook/instagram/`
3. In your dashboard → Connect Instagram account

**Webhook Endpoint:**
- `/webhook/instagram/` → Receives messages from Instagram
- `/api/connect/instagram/` → Connects account from frontend

### 4. **Unified Message Handler** ✅

**How it works:**
- All channels → Website Chat, Facebook, Instagram
- Same AI → Uses your organization's persona
- Same data → All leads stored in one place
- Same responses → Consistent experience

**Channels Supported:**
- ✅ Website Chat (ChatURL)
- ✅ Facebook Messenger
- ✅ Instagram Direct
- ✅ Email (via campaigns)

### 5. **Webhook & CRM Integration** ✅

**How it works:**
- Lead created → Webhook sent to n8n/HubSpot
- Background processing → Retries if failed
- HMAC signatures → Secure delivery
- n8n workflows → Can route to any CRM

**Endpoints:**
- Outbox system → Stores webhooks for delivery
- Retry logic → Exponential backoff
- Background task → Processes pending webhooks

**Command:**
- `python manage.py run_automations --task webhooks`

---

## 🚀 How to Use

### **Email Automation**

1. **Create a Campaign:**
   ```python
   from myApp.services_email import email_campaign_service
   
   campaign = email_campaign_service.create_campaign(
       organization=request.organization,
       name='Welcome Sequence',
       campaign_type='sequence',
       steps_data=[
           {'offset_days': 0, 'subject': 'Welcome!', 'body_template': '...'},
           {'offset_days': 3, 'subject': 'Follow-up', 'body_template': '...'}
       ]
   )
   ```

2. **Send Campaign:**
   ```python
   email_campaign_service.send_campaign(campaign, leads=[lead1, lead2])
   ```

3. **Automated Sequences:**
   - Run daily: `python manage.py run_automations --task email`
   - Or use Celery: `celery -A myProject beat` + `celery -A myProject worker`

### **Facebook Integration**

1. **Connect Page:**
   ```javascript
   // From frontend
   fetch('/api/connect/facebook/', {
       method: 'POST',
       body: JSON.stringify({
           access_token: 'user_access_token',
           page_id: 'your_page_id'
       })
   })
   ```

2. **Receive Messages:**
   - Configure webhook in Facebook Developer Console
   - Messages automatically handled by `/webhook/facebook/`

3. **AI Responds:**
   - Uses your organization's persona
   - Searches your properties
   - Creates leads automatically

### **Instagram Integration**

1. **Connect Account:**
   ```javascript
   fetch('/api/connect/instagram/', {
       method: 'POST',
       body: JSON.stringify({
           access_token: 'user_access_token',
           account_id: 'instagram_account_id'
       })
   })
   ```

2. **Receive Messages:**
   - Configure webhook in Facebook Developer Console
   - Messages automatically handled by `/webhook/instagram/`

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Customer Channels                     │
├─────────────────────────────────────────────────────────┤
│  Website Chat  │  Facebook  │  Instagram  │  Email     │
└────────┬────────┬───────────┬─────────────┬────────────┘
         │        │           │             │
         └────────┴───────────┴─────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Unified Message      │
         │  Handler              │
         └───────────┬────────────┘
                     │
         ┌───────────┴────────────┐
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌─────────────────┐
│  AI Chat Agent  │    │  Lead Capture   │
│  (Your Persona) │    │  Service        │
└────────┬────────┘    └────────┬────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Database (Your CRM)  │
         └───────────┬────────────┘
                     │
         ┌───────────┴────────────┐
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌─────────────────┐
│  Webhook Outbox │    │  Email Campaigns │
│  → n8n/HubSpot  │    │  Sequences       │
└─────────────────┘    └─────────────────┘
```

---

## 🔧 Configuration

### **Environment Variables:**

```bash
# Email
POSTMARK_API_TOKEN=your_postmark_token
POSTMARK_FROM_EMAIL=noreply@yourdomain.com

# Facebook/Instagram
FACEBOOK_VERIFY_TOKEN=your_verify_token
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret

# Celery (for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Webhooks
WEBHOOK_SIGNING_SECRET=your_webhook_secret
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/katek/ingest
```

### **Setup Background Tasks:**

**Option 1: Management Command (Simple)**
```bash
# Run daily via cron
0 2 * * * cd /path/to/project && python manage.py run_automations
```

**Option 2: Celery (Recommended)**
```bash
# Terminal 1: Celery Beat (scheduler)
celery -A myProject beat -l info

# Terminal 2: Celery Worker (processor)
celery -A myProject worker -l info
```

---

## 📝 Next Steps

1. **Set up Facebook App:**
   - Go to https://developers.facebook.com/
   - Create app → Add Messenger product
   - Configure webhook

2. **Configure Email Provider:**
   - Sign up for Postmark
   - Add API token to environment
   - Verify sender domain

3. **Set up Background Tasks:**
   - Install Redis: `brew install redis` (Mac) or use cloud Redis
   - Install Celery: Already in requirements.txt
   - Start Celery worker and beat

4. **Test the Flow:**
   - Create a test lead
   - Verify webhook sent
   - Check email received
   - Test Facebook message

---

## 🎯 Key Features

✅ **Unified AI** → Same persona across all channels  
✅ **Automatic Lead Capture** → No manual entry needed  
✅ **Email Sequences** → Follow-up automation  
✅ **Webhook Integration** → Sync with any CRM  
✅ **Background Processing** → Runs automatically  
✅ **Multi-channel** → Website, Facebook, Instagram  

All automations are **organization-scoped** - each company has their own data, AI persona, and settings! 🚀
