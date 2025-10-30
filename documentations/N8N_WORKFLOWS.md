# n8n Workflows Documentation

This document describes the n8n workflows needed to replace Celery/Redis for background job processing.

## Environment Variables

Set these in your n8n instance:

- `N8N_TOKEN`: Bearer token for authenticating API requests
- `N8N_HMAC_SECRET`: Secret for HMAC signature verification on callbacks
- `API_BASE_URL`: Base URL of your Django app (e.g., `https://your-app.com`)

## Workflow 1: Email Sequence Step Poller

**Purpose**: Poll for pending email sequence jobs and send them via Postmark.

**Trigger**: Cron (every 1 minute)

**Nodes**:

1. **Cron Trigger**
   - Schedule: `*/1 * * * *` (every minute)

2. **HTTP Request** (GET)
   - URL: `{{ $env.API_BASE_URL }}/api/jobs/next?kind=email_sequence_step&limit=50`
   - Method: GET
   - Headers:
     - `Authorization: Bearer {{ $env.N8N_TOKEN }}`
   - Response Format: JSON

3. **Split In Batches** (optional, if processing multiple)
   - Batch Size: 10

4. **For Each Job** (loop over jobs array):
   
   a. **HTTP Request** (POST to Postmark)
      - URL: `https://api.postmarkapp.com/email`
      - Method: POST
      - Headers:
        - `X-Postmark-Server-Token: {{ $env.POSTMARK_API_TOKEN }}`
        - `Content-Type: application/json`
      - Body:
        ```json
        {
          "From": "{{ $json.payload.from_email }}",
          "To": "{{ $json.payload.to_email }}",
          "Subject": "{{ $json.payload.subject }}",
          "HtmlBody": "{{ $json.payload.body }}",
          "MessageStream": "outbound"
        }
        ```
   
   b. **IF** (successful response):
      - **HTTP Request** (PATCH)
        - URL: `{{ $env.API_BASE_URL }}/api/jobs/{{ $json.id }}/`
        - Method: PATCH
        - Headers:
          - `Authorization: Bearer {{ $env.N8N_TOKEN }}`
          - `Content-Type: application/json`
        - Body:
          ```json
          {
            "status": "succeeded",
            "result": {"message_id": "{{ $json.MessageID }}"},
            "lease_id": "{{ $json.lease_id }}"
          }
          ```
   
   c. **IF** (error response):
      - **Code** (calculate backoff):
        ```javascript
        const attempts = $json.attempts + 1;
        const backoffMinutes = Math.pow(2, attempts); // Exponential backoff
        const nextAttempt = new Date(Date.now() + backoffMinutes * 60000);
        
        return {
          attempts: attempts,
          next_attempt_at: nextAttempt.toISOString()
        };
        ```
      
      - **HTTP Request** (PATCH)
        - URL: `{{ $env.API_BASE_URL }}/api/jobs/{{ $json.id }}/`
        - Method: PATCH
        - Headers:
          - `Authorization: Bearer {{ $env.N8N_TOKEN }}`
        - Body:
          ```json
          {
            "status": "failed",
            "error": "{{ $json.error }}",
            "attempts": {{ $json.attempts }},
            "next_attempt_at": "{{ $json.next_attempt_at }}",
            "lease_id": "{{ $json.lease_id }}"
          }
          ```

---

## Workflow 2: Webhook Delivery Poller

**Purpose**: Poll for pending webhook delivery jobs and send them to target URLs.

**Trigger**: Cron (every 1 minute)

**Nodes**:

1. **Cron Trigger**
   - Schedule: `*/1 * * * *`

2. **HTTP Request** (GET)
   - URL: `{{ $env.API_BASE_URL }}/api/jobs/next?kind=webhook_delivery&limit=200`
   - Headers:
     - `Authorization: Bearer {{ $env.N8N_TOKEN }}`

3. **For Each Job**:
   
   a. **Code** (generate HMAC signature):
      ```javascript
      const crypto = require('crypto');
      const timestamp = Math.floor(Date.now() / 1000);
      const body = JSON.stringify($json.payload);
      const message = `${timestamp}.${body}`;
      const signature = crypto.createHmac('sha256', process.env.N8N_HMAC_SECRET)
        .update(message)
        .digest('hex');
      
      return {
        signature: `sha256=${signature}`,
        timestamp: timestamp.toString()
      };
      ```
   
   b. **HTTP Request** (POST to target URL)
      - URL: `{{ $json.payload.target_url }}`
      - Method: POST
      - Headers:
        - `X-Signature: {{ $json.signature }}`
        - `X-Timestamp: {{ $json.timestamp }}`
        - `Content-Type: application/json`
      - Body: `{{ $json.payload.payload }}`
   
   c. **IF** (2xx response):
      - **HTTP Request** (PATCH)
        - URL: `{{ $env.API_BASE_URL }}/api/jobs/{{ $json.id }}/`
        - Body:
          ```json
          {
            "status": "succeeded",
            "lease_id": "{{ $json.lease_id }}"
          }
          ```
   
   d. **IF** (non-2xx response):
      - Calculate backoff (same as email workflow)
      - PATCH with failed status

---

## Workflow 3: Property Enrichment Executor

**Purpose**: Execute property enrichment jobs (can be triggered by job or cron).

**Trigger**: Cron (every 5 minutes) OR Webhook (from Django)

**Nodes**:

1. **Cron Trigger** (optional)
   - Schedule: `*/5 * * * *`
   
   OR **Webhook** (preferred)
   - Method: POST
   - Path: `/webhook/property-enrichment`

2. **HTTP Request** (GET)
   - URL: `{{ $env.API_BASE_URL }}/api/jobs/next?kind=property_enrichment&limit=10`

3. **For Each Job**:
   
   a. **Code** (enrichment logic)
      - Call external APIs (RentCast, etc.)
      - Generate narrative
      - Calculate estimates
   
   b. **HTTP Request** (POST callback)
      - URL: `{{ $env.API_BASE_URL }}/api/jobs/{{ $json.id }}/callback`
      - Method: POST
      - Headers:
        - `Authorization: Bearer {{ $env.N8N_TOKEN }}`
        - `X-Signature: {{ $json.signature }}`
        - `X-Timestamp: {{ $json.timestamp }}`
      - Body:
        ```json
        {
          "status": "succeeded",
          "result": {
            "narrative": "...",
            "estimate": 500000,
            "neighborhood_avg": 450000
          },
          "lease_id": "{{ $json.lease_id }}"
        }
        ```

---

## Workflow 4: Analytics Rollup Daily

**Purpose**: Daily rollup of analytics data.

**Trigger**: Cron (02:00 Asia/Manila)

**Nodes**:

1. **Cron Trigger**
   - Schedule: `0 2 * * *` (02:00 UTC = 10:00 Asia/Manila)
   - Timezone: Asia/Manila

2. **HTTP Request** (GET)
   - URL: `{{ $env.API_BASE_URL }}/api/jobs/next?kind=analytics_rollup&limit=100`

3. **For Each Job**:
   
   a. **Code** (aggregate data)
      - Calculate daily metrics per organization
      - Store in AnalyticsDaily model (if exists)
   
   b. **HTTP Request** (POST callback)
      - URL: `{{ $env.API_BASE_URL }}/api/jobs/{{ $json.id }}/callback`
      - Same signature/timestamp headers

---

## Common Patterns

### HMAC Signature Generation

For callback endpoints, always include:

```javascript
const crypto = require('crypto');
const timestamp = Math.floor(Date.now() / 1000).toString();
const body = JSON.stringify($json.body);
const message = `${timestamp}.${body}`;
const signature = crypto.createHmac('sha256', process.env.N8N_HMAC_SECRET)
  .update(message)
  .digest('hex');

// Headers:
// X-Signature: sha256=<hex>
// X-Timestamp: <unix_timestamp>
```

### Exponential Backoff

```javascript
const attempts = $json.attempts + 1;
const backoffMinutes = Math.pow(2, attempts); // 2, 4, 8, 16...
const maxAttempts = 5;

if (attempts >= maxAttempts) {
  // Mark as permanently failed
  return { status: "failed", permanently_failed: true };
}

const nextAttempt = new Date(Date.now() + backoffMinutes * 60000);
return {
  attempts: attempts,
  next_attempt_at: nextAttempt.toISOString()
};
```

### Error Handling

Always wrap workflows in error handlers:
- Log errors to n8n execution logs
- Update job status to "failed" with error message
- Include attempts and next_attempt_at for retries

---

## Testing

1. **Create a test job**:
   ```bash
   curl -X POST https://your-app.com/api/jobs/create/ \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "organization_id": "...",
       "kind": "email_sequence_step",
       "payload": {...}
     }'
   ```

2. **Verify poller picks it up**:
   - Check n8n execution logs
   - Verify job status changes to "in_progress"

3. **Verify callback**:
   - Check job status updates to "succeeded"
   - Verify JobEvent is created

---

## Monitoring

- Check `/admin/ingestion/health/` for job statuses
- Monitor JobTask counts by status/kind
- Check last callback timestamp per organization
- Alert on high failure rates or stale leases

