# 🔌 Webhook Testing Guide

## 📋 Current Webhook Configuration

### **Webhook URLs (from webhook.py)**

```python
# Chat Inquiry Webhook (Leads, Chat, Validation)
CHAT_INQUIRY_WEBHOOK = "https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545ponse"

# Property Listing Webhook (New Listings)
PROPERTY_LISTING_WEBHOOK = "https://katalyst-crm.fly.dev/webhook-test/7e36f0ef-e0b2-498d-886c-f06bef9afd80"
```

---

## 🧪 Method 1: Online Webhook Testers (Recommended for Quick Testing)

### **Option A: Webhook.site** ⭐ (Most Popular)

1. **Visit:** https://webhook.site
2. **Get your unique URL** (automatically generated)
3. **Copy the URL** (looks like: `https://webhook.site/12345678-abcd-...`)
4. **Temporarily replace** your webhook URLs in `webhook.py`:

```python
# TEMPORARY FOR TESTING
CHAT_INQUIRY_WEBHOOK = "https://webhook.site/YOUR-UNIQUE-ID"
PROPERTY_LISTING_WEBHOOK = "https://webhook.site/YOUR-UNIQUE-ID"
```

5. **Trigger a webhook** (submit lead form, upload property, etc.)
6. **Check webhook.site** - you'll see the request instantly!

**Features:**
- ✅ Real-time request display
- ✅ Shows headers, body, timestamp
- ✅ JSON formatting
- ✅ Request history
- ✅ No signup required

---

### **Option B: RequestBin** (by Pipedream)

1. **Visit:** https://requestbin.com
2. **Click "Create Request Bin"**
3. **Copy the endpoint URL**
4. **Replace** in `webhook.py` (same as above)
5. **Trigger webhook**
6. **View results** on RequestBin dashboard

**Features:**
- ✅ 48-hour history
- ✅ Shareable links
- ✅ Request comparison
- ✅ Free tier available

---

### **Option C: Beeceptor**

1. **Visit:** https://beeceptor.com
2. **Create endpoint** (e.g., `https://mytest.free.beeceptor.com`)
3. **Use as webhook URL**
4. **View incoming requests**

---

## 🐍 Method 2: Python Script to Test Your Actual Webhooks

Save this as `test_webhooks.py` in your project root:

```python
"""
Test if webhooks are accessible and responding
"""
import requests
import json
from datetime import datetime

# Your actual webhook URLs
CHAT_INQUIRY_WEBHOOK = "https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545ponse"
PROPERTY_LISTING_WEBHOOK = "https://katalyst-crm.fly.dev/webhook-test/7e36f0ef-e0b2-498d-886c-f06bef9afd80"

def test_chat_inquiry_webhook():
    """Test the chat inquiry webhook"""
    print("\n🧪 Testing Chat Inquiry Webhook...")
    print(f"URL: {CHAT_INQUIRY_WEBHOOK}")
    
    # Sample payload
    test_data = {
        "type": "chat_inquiry",
        "timestamp": datetime.now().isoformat(),
        "session_id": "test-session-12345",
        "lead": {
            "id": "test-lead-123",
            "name": "Test User",
            "phone": "+1-555-0123",
            "email": "test@example.com",
            "buy_or_rent": "rent",
            "budget_max": 3000,
            "beds": 2,
            "areas": "Los Angeles",
            "message": "Test webhook message"
        },
        "tracking": {
            "utm_source": "test",
            "utm_campaign": "webhook-test",
            "referrer": "manual-test"
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'PropertyListingBot/1.0 (Test)',
    }
    
    try:
        response = requests.post(
            CHAT_INQUIRY_WEBHOOK,
            json=test_data,
            headers=headers,
            timeout=10
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response Time: {response.elapsed.total_seconds():.2f}s")
        print(f"✅ Response Headers: {dict(response.headers)}")
        print(f"✅ Response Body: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Webhook is working!")
        else:
            print(f"⚠️  WARNING: Got status {response.status_code}")
            
        return True
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out (>10s)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to webhook URL")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_property_listing_webhook():
    """Test the property listing webhook"""
    print("\n🧪 Testing Property Listing Webhook...")
    print(f"URL: {PROPERTY_LISTING_WEBHOOK}")
    
    # Sample payload
    test_data = {
        "type": "property_listing",
        "timestamp": datetime.now().isoformat(),
        "session_id": "test-session-67890",
        "property": {
            "id": "test-property-456",
            "slug": "test-luxury-condo",
            "title": "Test Luxury Condo Downtown",
            "description": "Beautiful test property",
            "price_amount": 450000,
            "city": "Los Angeles",
            "area": "Downtown",
            "beds": 2,
            "baths": 2,
            "badges": "Test Listing"
        },
        "upload_info": {
            "upload_id": "test-upload-789",
            "validation_result": {},
            "missing_fields": []
        },
        "source": "webhook_test"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'PropertyListingBot/1.0 (Test)',
    }
    
    try:
        response = requests.post(
            PROPERTY_LISTING_WEBHOOK,
            json=test_data,
            headers=headers,
            timeout=10
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response Time: {response.elapsed.total_seconds():.2f}s")
        print(f"✅ Response Headers: {dict(response.headers)}")
        print(f"✅ Response Body: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Webhook is working!")
        else:
            print(f"⚠️  WARNING: Got status {response.status_code}")
            
        return True
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out (>10s)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to webhook URL")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔌 WEBHOOK TESTING TOOL")
    print("=" * 60)
    
    # Test both webhooks
    chat_ok = test_chat_inquiry_webhook()
    listing_ok = test_property_listing_webhook()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Chat Inquiry Webhook: {'✅ WORKING' if chat_ok else '❌ FAILED'}")
    print(f"Property Listing Webhook: {'✅ WORKING' if listing_ok else '❌ FAILED'}")
    print("\nNote: Even if webhooks fail, your app will continue working.")
    print("Webhooks are logged but non-blocking.")
    print("=" * 60)
```

**To Run:**
```bash
python test_webhooks.py
```

---

## 🛠️ Method 3: Django Management Command

Create this file: `myApp/management/commands/test_webhooks.py`

```python
"""
Django management command to test webhooks
Usage: python manage.py test_webhooks
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from myApp.webhook import (
    send_chat_inquiry_webhook,
    send_property_listing_webhook,
    send_property_chat_webhook,
    send_prompt_search_webhook
)


class Command(BaseCommand):
    help = 'Test all webhook endpoints'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS('🔌 Testing Webhooks...'))
        self.stdout.write("=" * 60)
        
        # Test 1: Chat Inquiry Webhook
        self.stdout.write("\n1️⃣  Testing Chat Inquiry Webhook...")
        chat_data = {
            "id": "test-123",
            "name": "Test User",
            "phone": "+1-555-0100",
            "email": "test@example.com",
            "buy_or_rent": "rent",
            "budget_max": 3000,
            "beds": 2,
            "areas": "Los Angeles",
            "interest_ids": "",
            "utm_source": "test",
            "utm_campaign": "webhook-test",
            "referrer": "manual",
            "session_id": "test-session",
            "timestamp": timezone.now().isoformat(),
            "message": "Test webhook from Django command"
        }
        
        result = send_chat_inquiry_webhook(chat_data)
        if result:
            self.stdout.write(self.style.SUCCESS('   ✅ Chat Inquiry: SUCCESS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Chat Inquiry: FAILED'))
        
        # Test 2: Property Listing Webhook
        self.stdout.write("\n2️⃣  Testing Property Listing Webhook...")
        property_data = {
            "id": "test-property-456",
            "slug": "test-condo",
            "title": "Test Luxury Condo",
            "description": "Test description",
            "price_amount": 450000,
            "city": "Los Angeles",
            "area": "Downtown",
            "beds": 2,
            "baths": 2,
            "floor_area_sqm": 100,
            "parking": True,
            "hero_image": "https://example.com/image.jpg",
            "badges": "Test",
            "created_at": timezone.now().isoformat(),
            "upload_id": "test-upload-789",
            "validation_result": {},
            "missing_fields": [],
            "consolidated_information": "Test",
            "session_id": "test-session",
            "timestamp": timezone.now().isoformat(),
            "source": "test"
        }
        
        result = send_property_listing_webhook(property_data)
        if result:
            self.stdout.write(self.style.SUCCESS('   ✅ Property Listing: SUCCESS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Property Listing: FAILED'))
        
        # Test 3: Property Chat Webhook
        self.stdout.write("\n3️⃣  Testing Property Chat Webhook...")
        chat_webhook_data = {
            "property_id": "test-prop-123",
            "property_slug": "test-property",
            "property_title": "Test Property",
            "property_city": "Los Angeles",
            "property_price": 3500,
            "message": "How much is rent?",
            "response": "The monthly rent is $3,500 USD.",
            "session_id": "test-session",
            "timestamp": timezone.now().isoformat(),
            "user_agent": "Test Agent",
            "ip_address": "127.0.0.1",
            "referrer": "http://localhost:8000/"
        }
        
        result = send_property_chat_webhook(chat_webhook_data)
        if result:
            self.stdout.write(self.style.SUCCESS('   ✅ Property Chat: SUCCESS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Property Chat: FAILED'))
        
        # Test 4: Prompt Search Webhook
        self.stdout.write("\n4️⃣  Testing Prompt Search Webhook...")
        search_data = {
            "prompt": "2 bedroom in LA under $3000",
            "results_count": 5,
            "session_id": "test-session",
            "buy_or_rent": "rent",
            "budget_max": 3000,
            "beds": 2,
            "areas": "Los Angeles",
            "property_ids": "id1,id2,id3",
            "timestamp": timezone.now().isoformat(),
            "utm_source": "test",
            "utm_campaign": "test",
            "referrer": "http://localhost:8000/"
        }
        
        result = send_prompt_search_webhook(search_data)
        if result:
            self.stdout.write(self.style.SUCCESS('   ✅ Prompt Search: SUCCESS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Prompt Search: FAILED'))
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.WARNING('ℹ️  Note: Check your CRM dashboard to verify data received'))
        self.stdout.write(self.style.WARNING('ℹ️  Failed webhooks are normal - app continues working'))
        self.stdout.write("=" * 60)
```

**To Run:**
```bash
python manage.py test_webhooks
```

---

## 🔍 Method 4: Check Webhooks from Your App

### **Enable Verbose Logging**

Add to `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'myApp.webhook': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### **Watch Console Output**

When running `python manage.py runserver`, you'll see:

**Successful webhook:**
```
INFO 2024-01-15 10:30:45 webhook Webhook sent successfully to https://katalyst-crm.fly.dev/webhook/...
```

**Failed webhook:**
```
ERROR 2024-01-15 10:30:45 webhook Failed to send webhook to https://...: Connection timeout
```

---

## 📊 Method 5: Test from Django Shell

```bash
python manage.py shell
```

```python
from myApp.webhook import send_chat_inquiry_webhook
from django.utils import timezone

# Test data
test_data = {
    "id": "test-123",
    "name": "Shell Test User",
    "phone": "+1-555-9999",
    "email": "shell@test.com",
    "buy_or_rent": "rent",
    "budget_max": 2500,
    "beds": 1,
    "areas": "Miami",
    "interest_ids": "",
    "utm_source": "django-shell",
    "utm_campaign": "manual-test",
    "referrer": "",
    "session_id": "shell-session",
    "timestamp": timezone.now().isoformat(),
    "message": "Testing from Django shell"
}

# Send webhook
result = send_chat_inquiry_webhook(test_data)
print(f"Webhook result: {result}")
```

---

## 🎯 Quick Test Checklist

### **Test Each Webhook Type:**

- [ ] **Chat Inquiry** - Submit lead form on homepage
- [ ] **Property Chat** - Ask question on property detail page
- [ ] **Buyer Chat** - Use new homepage chat widget
- [ ] **Prompt Search** - Search with AI prompt
- [ ] **Property Listing** - Upload property (complete validation)
- [ ] **Modal View** - Click property in chat widget

### **Verification Steps:**

1. **Start server:** `python manage.py runserver`
2. **Open console** - Watch for webhook messages
3. **Trigger action** - Submit form, chat, upload, etc.
4. **Check console** - Look for "Webhook sent successfully"
5. **Check CRM** - Verify data received (if accessible)

---

## 🚨 Troubleshooting

### **Problem: Webhooks timing out**

**Solution:**
```python
# In webhook.py, increase timeout
response = requests.post(
    url,
    json=data,
    headers=headers,
    timeout=30  # Increased from 10 to 30
)
```

### **Problem: CORS errors**

**Check headers in webhook.py:**
```python
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'PropertyListingBot/1.0',
    # Add if needed:
    'Access-Control-Allow-Origin': '*'
}
```

### **Problem: SSL certificate errors**

**Temporary fix for testing:**
```python
response = requests.post(
    url,
    json=data,
    headers=headers,
    timeout=10,
    verify=False  # Only for testing!
)
```

### **Problem: No webhook logs appearing**

**Add print statements:**
```python
def send_webhook(url: str, data: Dict[str, Any]) -> bool:
    print(f"🔌 Sending webhook to: {url}")
    print(f"📦 Payload: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(...)
        print(f"✅ Response: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
```

---

## 📝 Sample Curl Commands

### **Test Chat Inquiry Webhook:**
```bash
curl -X POST https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545ponse \
  -H "Content-Type: application/json" \
  -H "User-Agent: PropertyListingBot/1.0" \
  -d '{
    "type": "chat_inquiry",
    "timestamp": "2024-01-15T10:00:00Z",
    "session_id": "curl-test",
    "lead": {
      "name": "Curl Test",
      "phone": "+1-555-0000",
      "message": "Testing webhook with curl"
    }
  }'
```

### **Test Property Listing Webhook:**
```bash
curl -X POST https://katalyst-crm.fly.dev/webhook-test/7e36f0ef-e0b2-498d-886c-f06bef9afd80 \
  -H "Content-Type: application/json" \
  -H "User-Agent: PropertyListingBot/1.0" \
  -d '{
    "type": "property_listing",
    "timestamp": "2024-01-15T10:00:00Z",
    "property": {
      "title": "Curl Test Property",
      "price_amount": 500000,
      "city": "Los Angeles"
    }
  }'
```

---

## ✅ Best Testing Approach

### **For Quick Testing:**
1. Use **Webhook.site** (instant, visual feedback)
2. Replace webhook URLs temporarily
3. Trigger actions in your app
4. See requests in real-time

### **For Production Testing:**
1. Run **Python test script** (`test_webhooks.py`)
2. Check your actual CRM dashboard
3. Verify data format is correct
4. Monitor console logs

### **For Development:**
1. Use **Django management command**
2. Enable verbose logging
3. Watch console output
4. Test all webhook types

---

## 🎉 Success Indicators

**Webhook is working if you see:**
- ✅ Status Code: 200 (or 201/202)
- ✅ Response time < 5 seconds
- ✅ Console: "Webhook sent successfully"
- ✅ Data appears in CRM
- ✅ No exception errors

**Webhook failed but app still works:**
- ⚠️ Status Code: 400/404/500
- ⚠️ Timeout error
- ⚠️ Connection error
- ✅ Your app continues normally (non-blocking)

---

**Need help?** Check the console logs and run `test_webhooks.py` for detailed diagnostics!

