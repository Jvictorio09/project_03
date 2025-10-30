# 🤖 Complete N8N Automation Requirements Documentation

## Overview

This document provides **complete specifications** for all automation workflows that require n8n assistance in the Property Management Platform. Each automation is designed to handle specific business processes and integrate with external services.

---

## 🎯 **AUTOMATION WORKFLOWS REQUIRING N8N**

### **1. Property Enrichment ("Property IQ")** 🏠

**Purpose**: Automatically enrich property listings with market data, AI-generated narratives, and neighborhood analytics.

#### **Trigger Flow**
```
Django App → Outbox → n8n /enrich-property
```

#### **Input Payload**
```json
{
  "property_id": "uuid",
  "company_id": "uuid", 
  "address": "123 Main St",
  "city": "Manila",
  "price_amount": 5000000,
  "beds": 3,
  "baths": 2,
  "floor_area_sqm": 85,
  "property_type": "condo"
}
```

#### **N8N Processing Steps**
1. **RentCast API Lookup**: Fetch market data and comparable properties
2. **AI Narrative Generation**: Create property descriptions using OpenAI
3. **Neighborhood Analysis**: Calculate area averages and trends
4. **Data Validation**: Ensure data quality and completeness
5. **Image Enhancement**: Generate property descriptions from images

#### **Output Callback**
```json
{
  "property_id": "uuid",
  "estimate": 5200000,
  "neighborhood_avg": 4800000,
  "narrative": "This modern 3BR condo offers excellent value...",
  "source": "rentcast",
  "last_updated": "2024-01-15T10:30:00Z",
  "market_trends": {
    "appreciation_rate": 8.5,
    "days_on_market": 45,
    "comparable_sales": 12
  }
}
```

#### **Database Updates**
- `Property.narrative` ← AI-generated description
- `Property.estimate` ← Market value estimate
- `Property.neighborhood_avg` ← Area average price
- `Property.source` ← Data source identifier
- `Property.last_updated` ← Timestamp

---

### **2. Lead Scoring & Internal CRM Update** 📊

**Purpose**: Automatically score leads, update internal CRM system, and attach contextual notes.

#### **Trigger Flow**
```
Django App → Outbox → n8n /lead-created
```

#### **Input Payload**
```json
{
  "lead_id": "uuid",
  "company_id": "uuid",
  "email": "john@example.com",
  "phone": "+639171234567",
  "name": "John Doe",
  "property_id": "uuid",
  "buy_or_rent": "buy",
  "budget_max": 5000000,
  "beds": 2,
  "areas": "BGC, Makati",
  "utm": {
    "source": "facebook",
    "campaign": "summer2024"
  },
  "consent": true,
  "engagement_score": 75
}
```

#### **N8N Processing Steps**
1. **Lead Scoring Algorithm**: 
   - Budget vs Property Price Match (40%)
   - Location Preference Alignment (30%)
   - Contact Quality Score (20%)
   - Engagement Level (10%)
2. **Internal CRM Update**: Update lead record in your platform
3. **Note Attachment**: Add property context and scoring details
4. **Follow-up Scheduling**: Set reminders based on score
5. **Email Automation Trigger**: Start nurture sequence

#### **Output Callback**
```json
{
  "lead_id": "uuid",
  "crm": "internal",
  "status": "processed",
  "score": 85,
  "priority": "high",
  "message": "Lead processed successfully with score: 85/100",
  "follow_up_date": "2024-01-16T09:00:00Z"
}
```

#### **Database Updates**
- `Lead.webhook_sent` ← true
- `Lead.webhook_last_attempt` ← timestamp
- `Lead.score` ← calculated score
- `Lead.priority` ← high/medium/low
- `EventLog` ← Lead processing event

---

### **3. Email Campaign Dispatch** 📧

**Purpose**: Orchestrate targeted email campaigns with dynamic audience building and delivery tracking.

#### **Trigger Flow**
```
Django App → POST /campaign-dispatch
```

#### **Input Payload**
```json
{
  "campaign_id": "uuid",
  "company_id": "uuid",
  "audience_query": "budget_max > 5000000 AND beds >= 2",
  "template_id": "luxury_properties_v2",
  "sender": "sales@company.com",
  "subject": "Exclusive Properties in Your Budget Range",
  "schedule_time": "2024-01-16T10:00:00Z"
}
```

#### **N8N Processing Steps**
1. **Audience Building**: Query database using audience_query
2. **Template Rendering**: Personalize emails with property data
3. **Delivery via Resend**: Send emails with tracking
4. **Bounce Handling**: Process delivery failures
5. **Analytics Collection**: Track opens, clicks, conversions
6. **A/B Testing**: Test different subject lines/templates

#### **Output Callback**
```json
{
  "campaign_id": "uuid",
  "sent": 1250,
  "failed": 12,
  "status": "completed",
  "delivery_rate": 99.04,
  "open_rate": 23.5,
  "click_rate": 4.2,
  "unsubscribe_rate": 0.8
}
```

#### **Database Updates**
- `Campaign.status` ← completed/failed/partial
- `Campaign.sent_count` ← number sent
- `Campaign.failed_count` ← number failed
- `Campaign.metrics` ← performance data

---

### **4. Lead Nurturing Email Sequences** 💌

**Purpose**: Automated follow-up email sequences based on lead behavior and preferences.

#### **Trigger Flow**
```
Lead Created/Updated → n8n /lead-nurture-trigger
```

#### **Email Sequence Templates**

##### **Welcome Sequence (New Leads)**
- **Day 0**: Welcome + Property Recommendations
- **Day 3**: Market Insights + New Listings
- **Day 7**: Success Stories + Testimonials
- **Day 14**: Special Offers + Urgency

##### **Property Interest Sequence**
- **Day 1**: Detailed Property Information
- **Day 3**: Virtual Tour + Neighborhood Guide
- **Day 7**: Price Analysis + Market Comparison
- **Day 14**: Schedule Viewing + Contact Info

##### **Budget-Based Sequences**
- **Under Budget**: More Affordable Options
- **Over Budget**: Financing Options + Negotiation Tips
- **Perfect Match**: Urgency + Limited Time Offers

#### **Input Payload**
```json
{
  "lead_id": "uuid",
  "sequence_type": "welcome",
  "lead_data": {
    "name": "Maria Santos",
    "email": "maria@email.com",
    "budget_max": 5000000,
    "beds": 2,
    "areas": "BGC",
    "buy_or_rent": "buy"
  },
  "trigger_event": "lead_created",
  "personalization_data": {
    "recommended_properties": ["prop1", "prop2", "prop3"],
    "market_insights": "BGC prices up 8% this year"
  }
}
```

#### **N8N Processing Steps**
1. **Sequence Selection**: Choose appropriate email sequence
2. **Template Personalization**: Customize content for lead
3. **Property Matching**: Find relevant properties
4. **Email Scheduling**: Schedule emails with delays
5. **Behavior Tracking**: Monitor opens/clicks
6. **Sequence Adjustment**: Modify based on engagement

---

### **5. Analytics Rollups** 📈

**Purpose**: Generate periodic analytics snapshots for dashboard metrics and reporting.

#### **Trigger Flow**
```
n8n Cron (Every 6 hours) → GET /internal/metrics/snapshot?company_id=uuid
```

#### **Input Query**
```json
{
  "company_id": "uuid",
  "time_range": "24h",
  "metrics": [
    "properties_total",
    "leads_total", 
    "webhook_success_rate",
    "campaign_performance",
    "conversion_rates"
  ]
}
```

#### **N8N Processing Steps**
1. **Data Aggregation**: Collect metrics from multiple sources
2. **Trend Analysis**: Calculate growth rates and patterns
3. **Performance Scoring**: Rate different aspects of business
4. **Alert Generation**: Flag concerning trends
5. **Report Generation**: Create executive summaries

#### **Output Callback**
```json
{
  "company_id": "uuid",
  "properties_total": 245,
  "leads_total": 1234,
  "webhook_success_rate_24h": 98.5,
  "narratives_stale_count": 12,
  "campaign_performance": {
    "sent": 5000,
    "opened": 1250,
    "clicked": 312,
    "converted": 45
  },
  "trends": {
    "lead_growth": 15.2,
    "conversion_improvement": 8.7,
    "property_views_up": 23.1
  },
  "alerts": [
    "High bounce rate detected in recent campaign",
    "Lead response time above threshold"
  ]
}
```

---

### **6. Facebook/Instagram Channel Broker** 📱

**Purpose**: Handle Meta platform messaging integration for lead capture and automated responses.

#### **Trigger Flow**
```
Meta Webhook → n8n Verification → n8n Processing → Django Response → Meta Reply
```

#### **Input Payload**
```json
{
  "platform": "facebook",
  "user_id": "meta_user_12345",
  "message": "Looking for 3BR condo in BGC",
  "intents": ["property_search", "budget_inquiry"],
  "lead_captured": false,
  "session_data": {
    "previous_messages": 3,
    "last_property_viewed": "luxury-bgc-condo",
    "conversation_stage": "property_inquiry"
  }
}
```

#### **N8N Processing Steps**
1. **Message Verification**: Validate Meta webhook signature
2. **Intent Detection**: Analyze message for property interest
3. **Lead Capture**: Extract contact information
4. **Response Generation**: Create contextual replies
5. **Property Matching**: Find relevant properties
6. **Follow-up Scheduling**: Set reminders for sales team

#### **Output Response**
```json
{
  "reply_text": "I found 5 great 3BR condos in BGC! Here's the top match...",
  "intents": ["property_search", "budget_inquiry"],
  "lead_captured": true,
  "suggested_properties": ["property-uuid-1", "property-uuid-2"],
  "next_action": "schedule_viewing",
  "quick_replies": [
    "Send me details",
    "Schedule viewing", 
    "See more options"
  ]
}
```

---

### **7. Property Upload Validation Enhancement** ✅

**Purpose**: Enhance property uploads with additional validation and market data.

#### **Trigger Flow**
```
Property Upload → n8n /validate-property
```

#### **Input Payload**
```json
{
  "upload_id": "uuid",
  "property_data": {
    "title": "2BR Condo in BGC",
    "price_amount": 5000000,
    "city": "Taguig",
    "area": "BGC",
    "beds": 2,
    "baths": 2,
    "description": "Nice condo with good location"
  },
  "validation_result": {
    "completeness_score": 65,
    "missing_fields": ["floor_area", "parking", "amenities"]
  }
}
```

#### **N8N Processing Steps**
1. **Market Analysis**: Compare pricing with similar properties
2. **Completeness Check**: Identify missing critical information
3. **SEO Optimization**: Suggest better titles and descriptions
4. **Image Analysis**: Analyze uploaded photos for quality
5. **Competition Analysis**: Check similar listings in area
6. **Recommendation Generation**: Provide improvement suggestions

#### **Output Callback**
```json
{
  "upload_id": "uuid",
  "enhanced_data": {
    "suggested_title": "Modern 2BR Condo in BGC - Excellent Investment Opportunity",
    "market_price_range": "4.8M - 5.2M",
    "competition_count": 12,
    "seo_score": 78
  },
  "recommendations": [
    "Add floor area for better search visibility",
    "Include parking information",
    "Upload photos of bedrooms and living area",
    "Consider lowering price to 4.8M for faster sale"
  ],
  "validation_score": 85
}
```

---

### **8. Automated Follow-up Scheduling** 📅

**Purpose**: Automatically schedule follow-up activities based on lead behavior and scoring.

#### **Trigger Flow**
```
Lead Activity → n8n /schedule-followup
```

#### **Input Payload**
```json
{
  "lead_id": "uuid",
  "activity_type": "property_viewed",
  "activity_data": {
    "property_id": "uuid",
    "view_duration": 180,
    "pages_viewed": 3,
    "return_visitor": true
  },
  "lead_score": 75,
  "last_contact": "2024-01-10T14:30:00Z"
}
```

#### **N8N Processing Steps**
1. **Activity Analysis**: Determine lead engagement level
2. **Follow-up Type**: Choose appropriate follow-up method
3. **Timing Calculation**: Determine optimal contact time
4. **Task Creation**: Generate follow-up tasks for sales team
5. **Reminder Scheduling**: Set automated reminders
6. **Escalation Rules**: Apply escalation for high-value leads

#### **Output Callback**
```json
{
  "lead_id": "uuid",
  "follow_up_scheduled": true,
  "follow_up_type": "phone_call",
  "scheduled_time": "2024-01-16T10:00:00Z",
  "assigned_to": "sales_agent_1",
  "priority": "high",
  "notes": "High engagement on luxury BGC property, return visitor",
  "escalation_date": "2024-01-18T10:00:00Z"
}
```

---

## 🔧 **TECHNICAL IMPLEMENTATION REQUIREMENTS**

### **Webhook Security**
All webhooks use HMAC-SHA256 signature verification:
```python
def verify_webhook_signature(request):
    signature = request.headers.get('X-Signature')
    timestamp = request.headers.get('X-Timestamp')
    
    # Prevent replay attacks (5-minute window)
    if abs(current_time - request_time) > 300:
        return False
    
    # Verify signature
    expected_signature = hmac.new(
        settings.WEBHOOK_SIGNING_SECRET.encode('utf-8'),
        f"{timestamp}.{request.body.decode('utf-8')}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, f"sha256={expected_signature}")
```

### **Outbox Pattern Implementation**
```python
class OutboxMessage(models.Model):
    event_type = models.CharField(max_length=50)  # lead.created, property.enrich
    payload = models.JSONField()
    status = models.CharField(max_length=20)  # pending, sent, failed, retry
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
```

### **Error Handling & Retry Logic**
- **Exponential Backoff**: 1min, 5min, 15min retry intervals
- **Dead Letter Queue**: Failed messages after 3 attempts
- **Monitoring**: All webhook attempts logged to EventLog
- **Alerting**: Failed webhooks trigger email notifications

---

## 📊 **INTEGRATION ENDPOINTS SUMMARY**

| Endpoint | Method | Purpose | Trigger |
|----------|--------|---------|---------|
| `/internal/n8n/enrichment-complete` | POST | Property enrichment callback | After RentCast + AI processing |
| `/internal/n8n/lead-sync-status` | POST | Lead processing callback | After internal CRM update |
| `/internal/n8n/campaign-status` | POST | Email campaign callback | After email dispatch |
| `/internal/n8n/metrics-upsert` | POST | Analytics callback | After metrics calculation |
| `/internal/n8n/channel-message` | POST | Social media callback | After Meta message processing |
| `/internal/n8n/validation-complete` | POST | Property validation callback | After validation enhancement |
| `/internal/n8n/followup-scheduled` | POST | Follow-up scheduling callback | After task creation |

---

## 🎯 **PRIORITY IMPLEMENTATION ORDER**

### **Phase 1: Core Automations (Week 1-2)**
1. **Lead Scoring & Internal CRM Update** - Critical for lead management
2. **Property Enrichment** - Essential for listing quality
3. **Email Campaign Dispatch** - Basic email functionality

### **Phase 2: Advanced Automations (Week 3-4)**
4. **Lead Nurturing Sequences** - Automated follow-up
5. **Analytics Rollups** - Business intelligence
6. **Property Validation Enhancement** - Upload optimization

### **Phase 3: Channel Integration (Week 5-6)**
7. **Facebook/Instagram Broker** - Social media automation
8. **Automated Follow-up Scheduling** - Sales process optimization

---

## 📈 **SUCCESS METRICS**

### **Performance Targets**
- **Webhook Success Rate**: >99%
- **Processing Time**: Property enrichment <30s, Lead scoring <10s
- **Email Delivery Rate**: >98%
- **Lead Response Time**: <1 hour for high-priority leads
- **Campaign Open Rate**: >25%
- **Lead Conversion Rate**: >15%

### **Monitoring & Alerting**
- Webhook failure rate >5%
- Processing time >2x normal
- Queue depth >100 messages
- External API errors >10%
- Email bounce rate >5%
- Lead response time >2 hours

---

## 🚀 **DEPLOYMENT CHECKLIST**

### **Pre-Deployment**
- [ ] All webhook endpoints configured
- [ ] External API credentials configured
- [ ] Email service integration tested
- [ ] Internal CRM integration tested
- [ ] Error handling implemented
- [ ] Monitoring configured

### **Post-Deployment**
- [ ] Webhook signature verification working
- [ ] All automation flows tested
- [ ] Performance metrics within targets
- [ ] Error alerts configured
- [ ] Documentation updated
- [ ] Team training completed

This comprehensive documentation provides everything needed to implement all n8n automation workflows for the Property Management Platform.
