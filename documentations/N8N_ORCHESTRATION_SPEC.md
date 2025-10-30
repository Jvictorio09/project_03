## n8n Orchestration Specification — Django Integration

This document defines the complete integration between Django and n8n for email campaign orchestration, including implementation details, payload structures, and workflow specifications.

**Status**: ✅ IMPLEMENTED - Ready for testing with provided n8n workflow JSONs

### High-level responsibility split

- **Django (owns):**
  - Campaigns, Steps, Leads, EmailAccount (Gmail OAuth)
  - Rendering/personalization (Jinja-style), segmentation/audience
  - Computes exact send_at timestamps and sequencing
  - MessageLog states and analytics (opens, clicks, sent/failed)
  - Actual Gmail send and final state transitions
  - HMAC signature verification for security

- **n8n (owns):**
  - Waiting until send_at and retry backoff
  - Cron-like sweeps/safety nets
  - Orchestrating HTTP calls to Django and handling success/failure branches
  - No audience logic, no rendering logic

### Complete Integration Flow

#### 1. Campaign Send Flow (Django → n8n → Django)

```
Django Campaign Trigger
   ↓ (POST with HMAC)
n8n Workflow A Webhook
   ↓ (verify signature)
n8n Wait Node (until send_at)
   ↓ (at fire time)
n8n HTTP → Django /webhook/n8n/send-now/
   ↓ (render & send via Gmail)
Django updates MessageLog → returns {status: "sent"}
   ↓
n8n marks success
```

#### 2. Safety Sweep Flow (n8n → Django)

```
n8n Workflow B Cron (every 2 minutes)
   ↓ (GET)
Django /webhook/n8n/due-messages/
   ↓ (returns due messages)
n8n queues each via Workflow A
```

#### 3. Property Event Flow (Django → n8n → Django)

```
Django Property Event
   ↓ (POST with HMAC)
n8n Workflow C Webhook
   ↓ (get audience)
Django /webhook/n8n/audience-for-event/
   ↓ (for each lead)
n8n queues via Workflow A
```

### Visual Flow Reference

#### Success Path
```
Django (campaign trigger)
   ↓ POST /queue-campaign-send
n8n Webhook A (receives payload, validates HMAC)
   ↓
n8n Wait Node (delay until send_at)
   ↓
n8n HTTP Node → Django /webhook/n8n/send-now/
   ↓
Django sends via Gmail OAuth → updates MessageLog
   ↓
n8n receives 200 OK → success path
```

#### Error/Retry Path
```
n8n HTTP → /webhook/n8n/send-now/ → 5xx/network error
   ↓
Wait (2 min) → retry
   ↓
Wait (10 min) → retry
   ↓
If exhausted → n8n HTTP → /webhook/n8n/fail/ (with error_reason)
```

#### Cancellation Path
```
n8n HTTP → /webhook/n8n/send-now/ → Django replies "cancelled"
   ↓
n8n marks done (no email sent)
```

### Payload & Response Structure

#### Django → n8n (Queue Campaign Send)

**Headers:**
```
Content-Type: application/json
X-Timestamp: 1706361600
X-Signature: sha256=<HMAC-SHA256>
```

**Payload:**
```json
{
  "message_log_id": "12345",
  "campaign_id": "cmp_67890",
  "step_id": "1",
  "lead_id": "lead_abcd",
  "organization_id": "org_xyz",
  "send_at": "2025-10-30T12:00:00Z",
  "request_id": "12345",
  "created_at": "2025-10-29T19:42:58Z"
}
```

#### n8n → Django (/webhook/n8n/send-now/)

**Headers:**
```
Content-Type: application/json
X-Timestamp: 1706361600
X-Signature: sha256=<HMAC-SHA256>
```

**Payload:**
```json
{
  "message_log_id": "12345",
  "campaign_id": "cmp_67890",
  "step_id": "1",
  "lead_id": "lead_abcd",
  "organization_id": "org_xyz",
  "request_id": "12345",
  "created_at": "2025-10-30T12:00:00Z"
}
```

**Django Response:**
```json
{
  "status": "sent"
}
```
or
```json
{
  "status": "cancelled"
}
```

#### n8n → Django (/webhook/n8n/fail/)

**Payload:**
```json
{
  "campaign_id": "cmp_67890",
  "step_id": "1",
  "lead_id": "lead_abcd",
  "organization_id": "org_xyz",
  "error_reason": "Max retries exceeded"
}
```

#### Django → n8n (/webhook/n8n/due-messages/)

**Response:**
```json
{
  "messages": [
    {
      "message_log_id": "",
      "campaign_id": "cmp_67890",
      "step_id": "1",
      "lead_id": "lead_abcd",
      "organization_id": "org_xyz",
      "send_at": "2025-10-30T12:00:00Z",
      "request_id": "12345",
      "created_at": "2025-10-29T19:42:58Z"
    }
  ]
}
```

### Security Implementation

- **HMAC Signature**: `sha256=` + HMAC-SHA256(timestamp + "." + body, secret)
- **Timestamp**: Unix timestamp in `X-Timestamp` header
- **Replay Window**: 5 minutes maximum
- **Idempotency**: `request_id` prevents duplicate processing

### Django Endpoints (Implemented)

#### `/webhook/n8n/send-now/` (POST)
- **Purpose**: Execute email send at scheduled time
- **Auth**: HMAC signature verification
- **Input**: `{message_log_id, campaign_id, step_id, lead_id, organization_id, request_id, created_at}`
- **Behavior**:
  - Enforce idempotency by `request_id`
  - Validate campaign/step/lead state at execution time
  - If paused/unsubscribed/invalid: return `{status: "cancelled"}`
  - Else send via Gmail OAuth, update MessageLog to `sent`
- **Response**: `{status: "sent"}` or `{status: "cancelled"}`

#### `/webhook/n8n/fail/` (POST)
- **Purpose**: Record final failure after max retries
- **Auth**: HMAC signature verification
- **Input**: `{campaign_id, step_id, lead_id, organization_id, error_reason}`
- **Behavior**: Mark MessageLog `failed` with final error_reason
- **Response**: `{status: "failed_recorded"}`

#### `/webhook/n8n/due-messages/` (GET/POST)
- **Purpose**: Safety sweep - return due messages not yet sent
- **Response**: `{messages: [...]}` - small list of immediate first-step items
- **Behavior**: Returns active campaigns with step 1 (delay_hours=0) not yet sent

### n8n Workflows (JSON Files Provided)

#### Workflow A: Queue Campaign Send
- **File**: `n8n_json/Workflow_A_Queue_Campaign_Send.json`
- **Trigger**: Webhook POST
- **Features**:
  - HMAC signature verification
  - Wait until `send_at` timestamp
  - Exponential backoff retries (2min, 10min, 30min)
  - Calls Django `/webhook/n8n/send-now/`
  - Handles success/cancelled/failed responses

#### Workflow B: Due Messages Sweep
- **File**: `n8n_json/Workflow_B_Due_Messages_Sweep.json`
- **Trigger**: Cron every 2 minutes
- **Features**:
  - Fetches due messages from Django
  - Queues each via Workflow A
  - Logs sweep results

#### Workflow C: Property Event Campaigns
- **File**: `n8n_json/Workflow_C_Property_Event_Campaigns.json`
- **Trigger**: Webhook POST
- **Features**:
  - HMAC signature verification
  - Gets audience from Django
  - Determines send timing by event type
  - Queues messages via Workflow A

### MessageLog states (Django ledger)

- `pending`: queued for a specific `send_at` and handed to n8n
- `sending`: optional transitional while `/send-now` executes
- `sent`: success, store provider message id and timestamp
- `cancelled`: campaign paused, lead unsubscribed, or step invalid
- `failed`: final after retry exhaustion; persist error_reason

### Latest n8n Implementation Standards

#### Webhook Security
- **HMAC Verification**: All webhooks use HMAC-SHA256 with shared secret
- **Timestamp Validation**: 5-minute replay window to prevent replay attacks
- **Signature Format**: `sha256=` + HMAC-SHA256(timestamp + "." + body, secret)

#### Wait Node Configuration
- **Wait Until Date**: Uses absolute ISO-8601 timestamps for precise scheduling
- **Timezone Handling**: All times in UTC to avoid ambiguity

#### HTTP Request Best Practices
- **Timeout**: 30 seconds for all Django API calls
- **Retry Logic**: Explicit exponential backoff (2min → 10min → 30min)
- **Error Handling**: Separate error branches for different failure types
- **Headers**: Consistent HMAC signature headers across all requests

#### Error Handling Patterns
- **Transient Errors**: Automatic retry with exponential backoff
- **Permanent Errors**: Call Django `/fail` endpoint after max retries
- **Cancellation**: Graceful handling without retries
- **Logging**: Comprehensive logging at each step for debugging

### Security model

- **HMAC**: HMAC-SHA256 over a canonical JSON string (stable key order) using shared secret. Include `X-Signature` and `X-Signature-Timestamp` headers. Reject if missing/invalid.
- **Replay window**: Accept only if `now - created_at` ≤ short window (e.g., 5 minutes).
- **Idempotency**: `request_id = message_log_id`. If `/send-now` repeats, Django must return `{status: "sent"}` (no duplicate sends).
- **Transport**: HTTPS only. Rotate secrets periodically.

### Retry/backoff policy (suggested)

- Backoff: ~2m → ~10m → ~30m → ~2h (tune to Gmail API limits)
- Max attempts: small N (e.g., 4). After max → call `/fail` with `error_reason` from last attempt.

### Observability

- n8n: visual execution graph shows waits/retries/failures
- Django: MessageLog is the source of truth for UI counts and analytics; keep open pixel and tracked links unchanged

### Setup Instructions

#### 1. Environment Variables
Set these in your Django settings or environment:
```bash
USE_N8N_ORCHESTRATION=true
N8N_QUEUE_WEBHOOK_URL=https://your-n8n-instance.com/webhook/queue-campaign-send
N8N_HMAC_SECRET=your-shared-secret-key
```

#### 2. Import n8n Workflows
1. Import `Workflow_A_Queue_Campaign_Send.json` into n8n
2. Import `Workflow_B_Due_Messages_Sweep.json` into n8n  
3. Import `Workflow_C_Property_Event_Campaigns.json` into n8n
4. Set workflow variables:
   - `djangoBaseUrl`: Your Django instance URL
   - `n8nHmacSecret`: Same secret as Django
   - `workflowAWebhookUrl`: Workflow A webhook URL

#### 3. Test the Integration

**Smoke Test:**
1. Create a campaign with immediate first step
2. Send campaign → should queue via n8n
3. Check n8n execution logs
4. Verify MessageLog shows `sent` status

**Failure Test:**
1. Temporarily break Django `/send-now` endpoint
2. Send campaign → n8n should retry
3. Fix endpoint → should eventually succeed

**Cancellation Test:**
1. Send campaign
2. Pause campaign before execution
3. Verify `cancelled` response

### Test Matrix (Confidence Checks)

- ✅ **Single-lead smoke**: step 1 now → see Wait and `/send-now` firing; MessageLog pending→sent
- ✅ **Failure path**: make `/send-now` return non-200 once → n8n retries; final MessageLog shows single `sent`
- ✅ **Cancellation**: pause campaign before fire → `/send-now` returns `cancelled`; MessageLog `cancelled`
- ✅ **Property alert**: price change event → Workflow C fetches audience → enqueues via Workflow A

### Implementation notes for n8n (current best practices)

- Webhook node: enable POST, JSON response, do signature verification early (Function node) and return 401 on failure
- Wait node: use "Wait Until" with the absolute `send_at` value (UTC)
- HTTP Request node: set timeouts and retry behavior off at node-level; explicitly implement retry/backoff via the error branch for full control and auditability
- Error handling: use separate error branch; persist `error_reason` (status code/body excerpt) when calling `/fail`
- Cron node: keep interval small (1–5 minutes) for safety sweep; make Django return a small bounded list

### Example payloads

Request (Django → n8n Webhook A):

```json
{
  "message_log_id": "12345",
  "campaign_id": "cmp_67890",
  "step_id": "1",
  "lead_id": "lead_abcd",
  "organization_id": "org_xyz",
  "send_at": "2025-10-30T12:00:00Z",
  "request_id": "12345",
  "created_at": "2025-10-29T19:42:58Z"
}
```

Callback (n8n → Django `/send-now`):

```json
{
  "message_log_id": "12345",
  "request_id": "12345",
  "created_at": "2025-10-30T12:00:00Z"
}
```

`/send-now` success responses:

```json
{ "status": "sent" }
```

```json
{ "status": "cancelled" }
```

`/fail` (n8n → Django after max retries):

```json
{
  "message_log_id": "12345",
  "request_id": "12345",
  "error_reason": "Upstream 502 Bad Gateway from Gmail send",
  "created_at": "2025-10-30T14:40:00Z"
}
```

### Feature flag

- Add internal flag `use_n8n = true` (Django setting or per-organization) to switch orchestration. Keep Celery path intact for rollback but do not run workers when n8n is active.

---

This spec is the single source of truth for Django↔n8n orchestration. Keep the payload stable; extend with additive fields only.


