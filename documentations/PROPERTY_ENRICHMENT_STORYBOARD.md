# 🎬 Property Enrichment Storyboard

## Overview
This storyboard shows the **Property Enrichment ("Property IQ")** automation flow - how properties get automatically enhanced with market data, AI narratives, and neighborhood analytics.

---

## 📋 **SCENE 1: Property Gets Created**

### **What Happens:**
- User uploads a property through your platform
- Property gets saved to your database
- System automatically triggers enrichment

### **Visual:**
```
🏠 Property Created
├─ Title: "2BR Condo in BGC"
├─ Price: ₱5,000,000
├─ Basic info: beds, baths, location
└─ ⚡ AUTOMATIC TRIGGER → Enrichment Request
```

### **Behind the Scenes:**
```python
# In your create_property_from_upload() function
property_obj = Property.objects.create(...)

# AUTOMATICALLY triggers enrichment
send_property_enrichment_webhook({
    "property_id": str(property_obj.id),
    "title": "2BR Condo in BGC",
    "price_amount": 5000000,
    "city": "Taguig",
    "area": "BGC"
})
```

---

## 📋 **SCENE 2: n8n Gets the Data**

### **What Happens:**
- n8n receives the enrichment request
- Calls your webhook to get complete property data
- Prepares for enrichment processing

### **Visual:**
```
🔄 n8n Processing
├─ 📞 Calls: /webhook-test/enrich-property
├─ 📥 Gets: Complete property data
├─ 🧠 Prepares: For enrichment workflow
└─ ⚡ Starts: Market research & AI analysis
```

### **Data Flow:**
```json
// n8n calls your webhook with:
{
  "property_id": "550e8400-e29b-41d4-a716-446655440000",
  "company_id": "550e8400-e29b-41d4-a716-446655440001"
}

// Your system responds with:
{
  "status": "success",
  "property_data": {
    "title": "2BR Condo in BGC",
    "price_amount": 5000000,
    "city": "Taguig",
    "area": "BGC",
    "beds": 2,
    "baths": 2,
    "floor_area_sqm": 85
  }
}
```

---

## 📋 **SCENE 3: n8n Enriches the Property**

### **What Happens:**
- n8n runs multiple enrichment processes
- Gets market data, generates AI narrative, calculates trends
- Prepares enriched data for callback

### **Visual:**
```
🔍 n8n Enrichment Process
├─ 📊 RentCast API → Market data lookup
├─ 🤖 OpenAI → AI narrative generation  
├─ 📈 Analysis → Neighborhood trends
├─ ✅ Validation → Data quality check
└─ 📦 Package → Enriched data ready
```

### **Enrichment Steps:**
1. **Market Research**: "Similar properties in BGC average ₱4,800,000"
2. **AI Narrative**: "This modern 2BR condo offers excellent value..."
3. **Trend Analysis**: "Properties in this area increased 8% this year"
4. **Value Estimate**: "Market value: ₱5,200,000"

---

## 📋 **SCENE 4: Enriched Data Returns**

### **What Happens:**
- n8n calls back with enriched data
- Your system updates the property
- Property now has enhanced information

### **Visual:**
```
📞 n8n Callback
├─ 📤 Calls: /webhook/n8n/property-enrichment/
├─ 📊 Sends: Enriched data package
├─ ✅ Updates: Property in your database
└─ 🎉 Property: Now enhanced with market data
```

### **Callback Data:**
```json
{
  "property_id": "550e8400-e29b-41d4-a716-446655440000",
  "enrichment_data": {
    "narrative": "This modern 2BR condo offers excellent value in the heart of BGC. With proximity to major offices and shopping centers, it's perfect for young professionals seeking convenience and luxury.",
    "estimate": 5200000,
    "neighborhood_avg": 4800000,
    "source": "rentcast",
    "market_trends": {
      "appreciation_rate": 8.5,
      "days_on_market": 45,
      "comparable_sales": 12
    }
  }
}
```

---

## 📋 **SCENE 5: Property is Enhanced**

### **What Happens:**
- Property now has rich, market-backed information
- Better descriptions, pricing insights, neighborhood data
- Ready for better sales performance

### **Visual:**
```
🏠 Enhanced Property
├─ 📝 Narrative: "This modern 2BR condo offers excellent value..."
├─ 💰 Estimate: ₱5,200,000 (market value)
├─ 📊 Neighborhood Avg: ₱4,800,000
├─ 📈 Trend: +8.5% appreciation this year
└─ ✅ Source: rentcast (verified data)
```

### **Before vs After:**
```
BEFORE ENRICHMENT:
├─ Title: "2BR Condo in BGC"
├─ Price: ₱5,000,000
├─ Description: "Nice condo with good location"
└─ ❌ No market data

AFTER ENRICHMENT:
├─ Title: "2BR Condo in BGC" 
├─ Price: ₱5,000,000
├─ Description: "This modern 2BR condo offers excellent value..."
├─ ✅ Market Value: ₱5,200,000
├─ ✅ Neighborhood Avg: ₱4,800,000
├─ ✅ Trend: +8.5% appreciation
└─ ✅ AI-generated narrative
```

---

## 🎯 **THE COMPLETE FLOW**

### **Timeline:**
```
0:00 - Property created in your system
0:01 - Automatic enrichment trigger sent to n8n
0:02 - n8n gets property data from your webhook
0:30 - n8n completes enrichment (market data + AI)
0:31 - n8n calls back with enriched data
0:32 - Property updated with enhanced information
0:33 - Property ready for better sales performance
```

### **Key Benefits:**
- ✅ **Automatic**: No manual work needed
- ✅ **Fast**: Complete in ~30 seconds
- ✅ **Rich Data**: Market insights + AI narratives
- ✅ **Better Sales**: Enhanced properties convert better
- ✅ **Professional**: Every property looks expertly researched

---

## 🔧 **Technical Implementation**

### **Webhook Endpoints:**
- **Data Retrieval**: `https://mindalgos-project.fly.dev/webhook-test/enrich-property`
- **Enrichment Callback**: `https://mindalgos-project.fly.dev/webhook/n8n/property-enrichment/`

### **Database Fields Updated:**
- `Property.narrative` ← AI-generated description
- `Property.estimate` ← Market value estimate
- `Property.neighborhood_avg` ← Area average price
- `Property.last_updated` ← Enrichment timestamp
- `Property.source` ← Data source identifier

### **Error Handling:**
- ✅ Webhook failures don't break property creation
- ✅ All enrichment attempts are logged
- ✅ Failed enrichments can be retried
- ✅ System continues working even if n8n is down

---

## 🎬 **Storyboard Summary**

**The Property Enrichment flow is like having a real estate expert automatically research every property you list:**

1. **Property Created** → Automatic trigger
2. **n8n Gets Data** → Complete property information
3. **n8n Enriches** → Market research + AI analysis
4. **Data Returns** → Enhanced information
5. **Property Enhanced** → Ready for better sales

**Result**: Every property gets professional market analysis and AI-generated descriptions automatically, making them more attractive to buyers and helping them sell faster.

---

*This storyboard focuses on the Property Enrichment automation that's currently in motion with your n8n team.*

