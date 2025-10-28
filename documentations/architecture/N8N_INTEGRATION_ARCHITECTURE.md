# N8N Integration Architecture Guide

## Overview

This document provides n8n developers with a comprehensive understanding of the integration patterns, data flows, and architectural decisions for the Property Management Platform's n8n integration layer.

## System Architecture

The platform uses n8n as a **middleware orchestration layer** that sits between the Django application and external services. This architecture provides:

- **Reliability**: Outbox pattern ensures message delivery
- **Scalability**: Async processing of heavy operations
- **Flexibility**: Easy addition of new integrations
- **Monitoring**: Centralized webhook status tracking

## Integration Patterns

### 1. Property Enrichment ("Property IQ")

**Purpose**: Automatically enrich property listings with market data, AI-generated narratives, and neighborhood analytics.

#### Trigger Flow
```
Django App → Outbox → n8n /enrich-property
```

**Payload Structure**:
```json
{
  "property_id": "uuid",
  "company_id": "uuid", 
  "address": "123 Main St",
  "city": "Manila",
  "price_amount": 5000000,
  "beds": 3,
  "baths": 2
}
```

#### n8n Processing Steps
1. **RentCast API Lookup**: Fetch market data and comparable properties
2. **AI Narrative Generation**: Create property descriptions using OpenAI
3. **Neighborhood Analysis**: Calculate area averages and trends
4. **Data Validation**: Ensure data quality and completeness

#### Callback Flow
```
n8n → POST /internal/n8n/enrichment-complete
```

**Callback Payload**:
```json
{
  "property_id": "uuid",
  "estimate": 5200000,
  "neighborhood_avg": 4800000,
  "narrative": "This modern 3BR condo offers excellent value...",
  "source": "rentcast",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

**Database Updates**:
- `Property.narrative` ← AI-generated description
- `Property.estimate` ← Market value estimate
- `Property.neighborhood_avg` ← Area average price
- `Property.source` ← Data source identifier
- `Property.last_updated` ← Timestamp

---

### 2. Lead Scoring & CRM Push

**Purpose**: Automatically score leads, push to CRM systems, and attach contextual notes.

#### Trigger Flow
```
Django App → Outbox → n8n /lead-created
```

**Payload Structure**:
```json
{
  "lead_id": "uuid",
  "company_id": "uuid",
  "email": "john@example.com",
  "phone": "+639171234567",
  "property_id": "uuid",
  "utm": {
    "source": "facebook",
    "campaign": "summer2024"
  },
  "consent": true
}
```

#### n8n Processing Steps
1. **Lead Scoring Algorithm**: 
   - Budget vs Property Price Match (40%)
   - Location Preference Alignment (30%)
   - Contact Quality Score (20%)
   - Engagement Level (10%)
2. **CRM Integration**: Push to HubSpot/Salesforce/Pipedrive
3. **Note Attachment**: Add property context and scoring details
4. **Follow-up Scheduling**: Set reminders based on score

#### Callback Flow
```
n8n → POST /internal/n8n/lead-sync-status
```

**Callback Payload**:
```json
{
  "lead_id": "uuid",
  "crm": "hubspot",
  "status": "synced",
  "external_id": "hubspot_contact_12345",
  "message": "Lead synced successfully with score: 85/100"
}
```

**Database Updates**:
- `Lead.webhook_sent` ← true
- `Lead.webhook_last_attempt` ← timestamp
- `EventLog` ← Lead processing event

---

### 3. Email Campaign Dispatch

**Purpose**: Orchestrate targeted email campaigns with dynamic audience building and delivery tracking.

#### Trigger Flow
```
Django App → POST /campaign-dispatch
```

**Payload Structure**:
```json
{
  "campaign_id": "uuid",
  "company_id": "uuid",
  "audience_query": "budget_max > 5000000 AND beds >= 2",
  "template_id": "luxury_properties_v2",
  "sender": "sales@company.com"
}
```

#### n8n Processing Steps
1. **Audience Building**: Query database using audience_query
2. **Template Rendering**: Personalize emails with property data
3. **Delivery via Resend**: Send emails with tracking
4. **Bounce Handling**: Process delivery failures
5. **Analytics Collection**: Track opens, clicks, conversions

#### Callback Flow
```
n8n → POST /internal/n8n/campaign-status
```

**Callback Payload**:
```json
{
  "campaign_id": "uuid",
  "sent": 1250,
  "failed": 12,
  "status": "completed",
  "delivery_rate": 99.04
}
```

---

### 4. Analytics Rollups

**Purpose**: Generate periodic analytics snapshots for dashboard metrics and reporting.

#### Trigger Flow
```
n8n Cron (Every 6 hours) → GET /internal/metrics/snapshot?company_id=uuid
```

**Response Structure**:
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
    "clicked": 312
  }
}
```

#### Callback Flow
```
n8n → POST /internal/n8n/metrics-upsert
```

**Callback Payload**:
```json
{
  "company_id": "uuid",
  "properties_total": 245,
  "leads_total": 1234,
  "webhook_success_rate_24h": 98.5,
  "narratives_stale_count": 12,
  "last_updated": "2024-01-15T12:00:00Z"
}
```

---

### 5. Facebook/Instagram Channel Broker

**Purpose**: Handle Meta platform messaging integration for lead capture and automated responses.

#### Flow Architecture
```
Meta Webhook → n8n Verification → n8n Processing → Django Response → Meta Reply
```

#### Meta Webhook Processing
1. **Message Verification**: Validate Meta webhook signature
2. **Intent Detection**: Analyze message for property interest
3. **Lead Capture**: Extract contact information
4. **Response Generation**: Create contextual replies

#### n8n → Django Communication
```
n8n → POST /internal/n8n/channel-message
```

**Payload Structure**:
```json
{
  "platform": "facebook",
  "user_id": "meta_user_12345",
  "message": "Looking for 3BR condo in BGC",
  "intents": ["property_search", "budget_inquiry"],
  "lead_captured": false,
  "session_data": {
    "previous_messages": 3,
    "last_property_viewed": "luxury-bgc-condo"
  }
}
```

#### Django Response
```json
{
  "reply_text": "I found 5 great 3BR condos in BGC! Here's the top match...",
  "intents": ["property_search", "budget_inquiry"],
  "lead_captured": true,
  "suggested_properties": ["property-uuid-1", "property-uuid-2"],
  "next_action": "schedule_viewing"
}
```

---

## Technical Implementation Details

### Webhook Security

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

### Outbox Pattern Implementation

The system uses a database outbox pattern for reliable message delivery:

```python
class OutboxMessage(models.Model):
    event_type = models.CharField(max_length=50)  # lead.created, property.enrich
    payload = models.JSONField()
    status = models.CharField(max_length=20)  # pending, sent, failed, retry
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
```

### Error Handling & Retry Logic

- **Exponential Backoff**: 1min, 5min, 15min retry intervals
- **Dead Letter Queue**: Failed messages after 3 attempts
- **Monitoring**: All webhook attempts logged to EventLog
- **Alerting**: Failed webhooks trigger email notifications

### Data Models

#### Property Enrichment Fields
```python
class Property(models.Model):
    # Enrichment fields
    narrative = models.TextField(blank=True)
    estimate = models.IntegerField(null=True, blank=True)
    neighborhood_avg = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=50, blank=True)
```

#### Lead Processing Fields
```python
class Lead(models.Model):
    # Processing fields
    autoresponder_sent = models.BooleanField(default=False)
    webhook_sent = models.BooleanField(default=False)
    webhook_attempts = models.IntegerField(default=0)
    webhook_last_attempt = models.DateTimeField(null=True, blank=True)
```

## N8N Workflow Best Practices

### 1. Error Handling
- Always implement try-catch blocks
- Log errors with context (property_id, lead_id, etc.)
- Set appropriate retry policies
- Use dead letter queues for failed messages

### 2. Data Validation
- Validate required fields before processing
- Sanitize input data
- Check data types and ranges
- Handle missing optional fields gracefully

### 3. Performance Optimization
- Use parallel processing where possible
- Implement caching for external API calls
- Batch operations when feasible
- Monitor execution times

### 4. Monitoring & Logging
- Log all major workflow steps
- Include correlation IDs for tracing
- Monitor success/failure rates
- Set up alerts for critical failures

### 5. Security Considerations
- Always verify webhook signatures
- Use HTTPS for all communications
- Implement rate limiting
- Sanitize data before external API calls

## Integration Endpoints Summary

| Endpoint | Method | Purpose | Trigger |
|----------|--------|---------|---------|
| `/internal/n8n/enrichment-complete` | POST | Property enrichment callback | After RentCast + AI processing |
| `/internal/n8n/lead-sync-status` | POST | Lead processing callback | After CRM sync |
| `/internal/n8n/campaign-status` | POST | Email campaign callback | After email dispatch |
| `/internal/n8n/metrics-upsert` | POST | Analytics callback | After metrics calculation |
| `/internal/n8n/channel-message` | POST | Social media callback | After Meta message processing |

## Development Workflow

### 1. Local Development
- Use ngrok for webhook testing
- Mock external APIs for development
- Test with sample data from the platform

### 2. Testing Strategy
- Unit tests for individual workflow steps
- Integration tests for complete flows
- Load testing for high-volume scenarios
- Error scenario testing

### 3. Deployment Process
- Deploy to staging environment first
- Test with real data (limited volume)
- Monitor for 24 hours before production
- Gradual rollout with feature flags

## Monitoring & Observability

### Key Metrics to Track
- **Webhook Success Rate**: Target >99%
- **Processing Time**: Property enrichment <30s, Lead scoring <10s
- **Error Rates**: By workflow type and error category
- **Queue Depth**: Outbox message backlog
- **External API Health**: RentCast, CRM, Email service uptime

### Alerting Thresholds
- Webhook failure rate >5%
- Processing time >2x normal
- Queue depth >100 messages
- External API errors >10%

This architecture provides a robust, scalable foundation for integrating the Property Management Platform with external services through n8n, ensuring reliable data processing and seamless user experiences.
