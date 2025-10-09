# 🚀 Webhook Testing - Quick Start

## 📌 Your Webhook URLs

```
Chat/Lead Webhook:
https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545ponse

Property Listing Webhook:
https://katalyst-crm.fly.dev/webhook-test/7e36f0ef-e0b2-498d-886c-f06bef9afd80
```

---

## ⚡ Quick Test (30 seconds)

### **Method 1: Python Script** ⭐ Recommended
```bash
python test_webhooks.py
```

### **Method 2: Django Command**
```bash
python manage.py test_webhooks
```

### **Method 3: Online Tester**
1. Visit: https://webhook.site
2. Copy your unique URL
3. Replace in `webhook.py` temporarily
4. Test your app (submit form, upload property, etc.)
5. See requests in real-time!

---

## 🎯 What Each Webhook Does

| Webhook Type | When It Fires | What Data It Sends |
|--------------|---------------|-------------------|
| **Chat Inquiry** | Lead form submission, validation chat | Lead info, tracking data |
| **Property Chat** | Property Q&A chat, modal views | Property info, messages |
| **Buyer Chat** | Homepage chat widget | Search query, results |
| **Prompt Search** | AI search on results page | Search terms, filters |
| **Property Listing** | New property created | Full property details |

---

## ✅ Quick Verification

**Run this to test everything:**
```bash
python test_webhooks.py
```

**Expected output:**
```
🧪 Testing Chat Inquiry Webhook...
✅ Status Code: 200
✅ SUCCESS: Webhook is working!

🧪 Testing Property Listing Webhook...
✅ Status Code: 200
✅ SUCCESS: Webhook is working!

📊 SUMMARY
Chat Inquiry Webhook:     ✅ WORKING
Property Listing Webhook: ✅ WORKING
```

---

## 🔧 Test from Your App

### **Test Lead Form:**
1. Go to: `http://localhost:8000/`
2. Scroll down and fill out lead form
3. Submit
4. Check console: `Webhook sent successfully...`

### **Test Manual Form Listing:**
1. Go to: `http://localhost:8000/manual-form-listing/`
2. Fill out form with test data
3. Submit
4. Check console for webhook log

### **Test Homepage Chat:**
1. Go to: `http://localhost:8000/`
2. Click chat widget (bottom-right)
3. Type: "2 bedroom in LA"
4. Submit
5. Check console for webhook log

---

## 📊 Check if Webhooks Are Working

### **Option A: Console Logs**
When running server, watch for:
```
INFO ... webhook Webhook sent successfully to https://...
```

### **Option B: Django Shell**
```bash
python manage.py shell
```

```python
from myApp.webhook import send_chat_inquiry_webhook
from django.utils import timezone

data = {
    "id": "test",
    "name": "Test",
    "phone": "555-0100",
    "email": "test@test.com",
    "buy_or_rent": "rent",
    "budget_max": 3000,
    "beds": 2,
    "areas": "LA",
    "session_id": "test",
    "timestamp": timezone.now().isoformat(),
    "message": "Test from shell"
}

result = send_chat_inquiry_webhook(data)
print(f"Success: {result}")
```

---

## 🐛 Troubleshooting

### **Webhooks failing?**
✅ **This is OK!** Your app continues working normally.

Webhooks are:
- ✅ Non-blocking (won't stop your app)
- ✅ Logged (you'll see errors in console)
- ✅ Optional (app works without them)

### **Want to debug?**
Add print statements in `webhook.py`:
```python
def send_webhook(url: str, data: Dict[str, Any]) -> bool:
    print(f"🔌 Sending to: {url}")
    print(f"📦 Data: {data}")
    
    try:
        response = requests.post(...)
        print(f"✅ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
```

---

## 📁 Files Created

```
✅ WEBHOOK_TESTING_GUIDE.md      - Complete testing guide
✅ test_webhooks.py               - Quick Python test script
✅ myApp/management/commands/     - Django management command
   └── test_webhooks.py
✅ WEBHOOK_QUICK_START.md        - This file
```

---

## 💡 Pro Tips

1. **Use webhook.site** for quick visual testing
2. **Run test_webhooks.py** for production webhook testing
3. **Check console logs** during development
4. **Don't worry about failures** - they won't break your app
5. **Verify in CRM dashboard** if webhooks are critical

---

## 🎉 All Done!

You now have **4 ways** to test webhooks:
1. ⚡ Python script: `python test_webhooks.py`
2. 🔧 Django command: `python manage.py test_webhooks`
3. 🌐 Online tester: webhook.site
4. 🖥️ Your app: Submit forms, upload properties, use chat

**Need detailed docs?** See `WEBHOOK_TESTING_GUIDE.md`

---

**Quick test now:**
```bash
python test_webhooks.py
```

