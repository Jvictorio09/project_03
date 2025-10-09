# 🔌 Webhook Integration - AI Prompt Search

## ✅ What I Built For You

I've created an **interactive AI prompt search** that:
1. ✅ Sends user's search query to your **Katalyst CRM webhook**
2. ✅ Waits for and displays the **webhook response**
3. ✅ Shows **matching properties** based on AI analysis
4. ✅ Works **without leaving the homepage** (HTMX powered)
5. ✅ Displays **webhook status** visually

---

## 🎯 Your Production Webhook

```
https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545
```

**This webhook is now integrated** into the homepage AI search form!

---

## 📋 What Was Added

### **1. New View Function**
**File:** `myApp/views.py` (lines 1580-1715)

**Function:** `ai_prompt_search()`

**What it does:**
1. Receives AI prompt from user
2. Processes it locally with `process_ai_search_prompt()`
3. Finds matching properties
4. **Sends complete data to your webhook**
5. **Waits for webhook response**
6. Displays response + properties

---

### **2. New URL Route**
**File:** `myApp/urls.py`

```python
path("search/ai-prompt/", views.ai_prompt_search, name="ai_prompt_search"),
```

---

### **3. New Template Partial**
**File:** `myApp/templates/partials/ai_prompt_results.html`

**Displays:**
- ✅ Webhook response (if received)
- ✅ AI analysis message
- ✅ Search criteria badges
- ✅ Property cards (up to 6)
- ✅ "View All Results" link

---

### **4. Updated Homepage Form**
**File:** `myApp/templates/home.html` (lines 30-91)

**Changes:**
- ✅ Now uses **HTMX** instead of GET form
- ✅ Posts to `/search/ai-prompt/`
- ✅ Shows **loading indicator** with "🔌 Sending to webhook..."
- ✅ Displays results **on same page**
- ✅ Shows **webhook response** visually

---

## 🚀 How It Works

### **User Flow:**

```
1. User visits homepage
   ↓
2. User types: "2 bedroom condo in LA under $3500"
   ↓
3. User clicks "Find My Perfect Home"
   ↓
4. Loading indicator appears: "🔌 Sending to webhook..."
   ↓
5. HTMX sends POST to /search/ai-prompt/
   ↓
6. Backend processes:
   - Extracts: city=LA, beds=2, price=3500
   - Finds matching properties in database
   - Sends data to YOUR WEBHOOK
   - Waits for webhook response
   ↓
7. Webhook responds with data
   ↓
8. Results appear on homepage:
   ✅ Green box: "Webhook Response Received"
   ✅ AI message: "Perfect! I found 4 properties..."
   ✅ Property cards with images
   ✅ "View All Results" button
```

---

## 📤 Webhook Payload Structure

Your webhook receives this JSON:

```json
{
  "type": "ai_prompt_search",
  "timestamp": "2024-01-15T10:30:45Z",
  "session_id": "abc123xyz",
  "prompt": "2 bedroom condo in LA under $3500",
  
  "extracted_params": {
    "city": "Los Angeles",
    "beds": 2,
    "price_max": 3500,
    "buy_or_rent": "rent",
    "keywords": ["condo"]
  },
  
  "results_count": 4,
  
  "properties": [
    {
      "id": "uuid-123",
      "slug": "modern-2br-condo",
      "title": "Modern 2BR Condo Downtown",
      "price": 3200,
      "city": "Los Angeles",
      "area": "Downtown",
      "beds": 2,
      "baths": 2
    },
    // ... up to 6 properties
  ],
  
  "tracking": {
    "utm_source": "",
    "utm_campaign": "",
    "referrer": "https://..."
  }
}
```

---

## 📥 Webhook Response Options

Your webhook can respond with JSON:

### **Option 1: Simple Message**
```json
{
  "message": "Search received and processed successfully!"
}
```

### **Option 2: Detailed Response**
```json
{
  "message": "Found great matches in your area",
  "data": {
    "recommendations": ["Check property #1", "Property #3 is popular"],
    "insights": "High demand area",
    "next_steps": "Schedule viewing?"
  }
}
```

### **Option 3: Just HTTP 200**
Even an empty 200 response works - we'll show success!

---

## 🎨 What Users See

### **Before Submission:**
```
┌─────────────────────────────────────────┐
│  🌟 Tell us what you're looking for     │
│                                         │
│  [Textarea: Describe your ideal home]  │
│                                         │
│  💡 Be specific about location...       │
│                                         │
│  🤖 AI-powered  🔗 Webhook  ⚡ Instant   │
│  [ Find My Perfect Home ]               │
└─────────────────────────────────────────┘
```

### **During Search:**
```
┌─────────────────────────────────────────┐
│  ⏳ 🔌 Sending to webhook and finding   │
│     perfect matches...                  │
└─────────────────────────────────────────┘
```

### **After Search:**
```
┌─────────────────────────────────────────┐
│  ✅ Webhook Response Received           │
│  Your custom message from webhook       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  💡 AI Search Results                   │
│  Perfect! I found 4 properties...       │
│                                         │
│  📍 Los Angeles  🏠 2+ beds  💰 <$3500  │
└─────────────────────────────────────────┘

┌───────────┐ ┌───────────┐ ┌───────────┐
│ Property 1│ │ Property 2│ │ Property 3│
│  $3,200   │ │  $3,400   │ │  $3,100   │
│ 2 bed•2ba │ │ 2 bed•2ba │ │ 2 bed•1ba │
└───────────┘ └───────────┘ └───────────┘

[ View All 4 Results → ]
```

---

## 🧪 How to Test

### **Method 1: Test on Homepage**

1. **Start server:**
   ```bash
   python manage.py runserver
   ```

2. **Visit:** `http://localhost:8000/`

3. **Type in AI search:**
   ```
   I need a 2 bedroom condo in Los Angeles under $3500
   ```

4. **Click:** "Find My Perfect Home"

5. **Watch:**
   - Loading indicator appears
   - Console shows webhook request
   - Results appear with webhook response

6. **Check console output:**
   ```
   ✅ Webhook sent successfully. Status: 200
   ```

---

### **Method 2: Check Webhook Response**

**In your terminal (while server runs), you'll see:**

```
✅ Webhook sent successfully. Status: 200
```

**Or if webhook fails:**
```
⚠️ Webhook error: Connection timeout
```

**Don't worry!** Even if webhook fails, the search still works and shows results!

---

## 📊 What Data Gets Sent

**Every search sends:**
- ✅ User's original prompt
- ✅ Extracted search parameters (city, beds, price, etc.)
- ✅ Matching properties (up to 6)
- ✅ Total results count
- ✅ Session tracking
- ✅ UTM parameters
- ✅ Timestamp

**You receive:**
- ✅ Complete user intent
- ✅ Search analytics
- ✅ Property recommendations
- ✅ User behavior data

---

## 🔧 Customization Options

### **Change Number of Properties Sent:**
Edit `views.py` line 1616:
```python
top_properties = qs[:6]  # Change to 10, 20, etc.
```

### **Customize Response Message:**
Edit `views.py` lines 1684-1702:
```python
if top_properties.count() > 0:
    response_message = "Your custom message here!"
```

### **Change Webhook URL:**
Edit `views.py` line 1619:
```python
webhook_url = "https://your-new-webhook-url.com"
```

### **Add More Data to Webhook:**
Edit `views.py` lines 1620-1650 to add fields to `webhook_payload`

---

## 🎯 Test Queries to Try

```
✅ "2 bedroom condo in Los Angeles under $3500"
   → Should extract: beds=2, city=LA, price=3500

✅ "3 bed house in Miami with pool"
   → Should extract: beds=3, city=Miami, keywords=[house, pool]

✅ "apartment with gym and parking under $4000"
   → Should extract: price=4000, keywords=[apartment, gym, parking]

✅ "luxury condo in downtown Chicago"
   → Should extract: city=Chicago, keywords=[luxury, condo]
```

---

## 🐛 Troubleshooting

### **Webhook not responding?**
✅ **This is OK!** Search still works
- Results still display
- Properties still shown
- User experience unchanged

### **Want to see webhook details?**
Check your CRM dashboard for incoming data

### **Webhook timing out?**
Increase timeout in `views.py` line 1667:
```python
timeout=30  # Changed from 10 to 30 seconds
```

### **Need to debug payload?**
Add print before sending (line 1656):
```python
print(f"📤 Sending to webhook:")
print(json.dumps(webhook_payload, indent=2))
```

---

## 📈 Analytics You Get

From every search, you receive:
- 📊 User search intent (raw prompt)
- 🎯 Extracted parameters (structured data)
- 🏠 Matching properties
- 📍 Location preferences
- 💰 Budget information
- 🔑 Keyword interests
- 👤 Session tracking
- 📅 Timestamp
- 🔗 Referrer tracking

---

## ✅ Success Checklist

Test these to verify everything works:

- [ ] Homepage loads correctly
- [ ] AI search form appears
- [ ] Can type in textarea
- [ ] Click "Find My Perfect Home" button
- [ ] Loading indicator appears
- [ ] Console shows: "✅ Webhook sent successfully"
- [ ] Results appear below form
- [ ] Green "Webhook Response Received" box shows
- [ ] Property cards display
- [ ] "View All Results" link works
- [ ] No JavaScript errors in console
- [ ] Works on mobile

---

## 🎉 Summary

**You now have:**
✅ AI prompt search integrated with YOUR webhook
✅ Real-time webhook response display
✅ Beautiful HTMX-powered UX
✅ Complete analytics sent to CRM
✅ Non-blocking (works even if webhook fails)
✅ Production-ready code

**Your webhook receives:**
✅ Every search query
✅ Extracted parameters
✅ Matching properties
✅ Full user context

**Test it now:**
```bash
python manage.py runserver
# Visit http://localhost:8000/
# Type: "2 bedroom in LA under $3500"
# Click: "Find My Perfect Home"
# Watch the magic! 🎉
```

---

## 📞 Quick Reference

**Webhook URL:**
```
https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545
```

**Endpoint:**
```
POST /search/ai-prompt/
```

**Files Modified:**
- `myApp/views.py` (+136 lines)
- `myApp/urls.py` (+1 route)
- `myApp/templates/home.html` (updated form)
- `myApp/templates/partials/ai_prompt_results.html` (new)

**Test Command:**
```bash
python manage.py runserver
```

---

**Ready to test? Start your server and try it! 🚀**

