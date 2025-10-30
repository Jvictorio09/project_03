# API Contracts - Dashboard & Jobs

## Jobs API (n8n Integration)

### GET /api/jobs/next
Poll endpoint for n8n to fetch pending jobs.

**Query Parameters:**
- `kind` (optional): Filter by job kind (e.g., `email_sequence_step`, `webhook_delivery`)
- `limit` (optional, default: 50): Maximum number of jobs to return

**Headers:**
- `Authorization: Bearer <N8N_TOKEN>`

**Response:**
```json
[
  {
    "id": "uuid",
    "kind": "email_sequence_step",
    "payload": {...},
    "attempts": 0,
    "lease_id": "uuid",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

**Status Codes:**
- `200`: Success
- `401`: Missing or invalid token
- `500`: Server error

**Behavior:**
- Leases up to N pending jobs where `next_attempt_at <= now()`
- Sets status to `in_progress` and assigns `lease_id`
- Returns array of jobs (id, kind, payload, attempts, lease_id)

---

### PATCH /api/jobs/<uuid>
Update job status and results.

**Headers:**
- `Authorization: Bearer <N8N_TOKEN>`

**Body:**
```json
{
  "status": "succeeded|failed",
  "result": {...},  // optional
  "error": "...",   // optional
  "attempts": 1,
  "next_attempt_at": "2024-01-01T00:00:00Z",  // optional, for retries
  "lease_id": "uuid"  // required, must match current lease
}
```

**Response:**
```json
{
  "status": "success",
  "job_id": "uuid"
}
```

**Status Codes:**
- `200`: Success
- `401`: Missing or invalid token
- `409`: Lease ID mismatch
- `404`: Job not found

**Behavior:**
- Validates `lease_id` matches current job lease
- Updates status and bookkeeping fields
- Creates JobEvent log entry

---

### POST /api/jobs/<uuid>/callback
Webhook callback endpoint (same contract as PATCH).

**Headers:**
- `Authorization: Bearer <N8N_TOKEN>`
- `X-Signature: sha256=<hex>` (HMAC of raw body + timestamp)
- `X-Timestamp: <unix_timestamp>`

**Body:** Same as PATCH

**Security:**
- HMAC signature verification required
- Timestamp must be within 5 minutes of current time
- Secret: `N8N_HMAC_SECRET`

---

## Dashboard API

### GET /api/dashboard/timeseries
Get timeseries data for dashboard charts.

**Query Parameters:**
- `range`: `7d|30d|90d` (default: `7d`)

**Response:**
```json
{
  "series": {
    "leads_created": [
      {"date": "2024-01-01", "count": 5},
      {"date": "2024-01-02", "count": 8},
      ...
    ]
  }
}
```

**Behavior:**
- Calendar days, zero-filled for missing days
- Timezone: Asia/Manila
- Organization-scoped
- Only includes connected channels

---

### GET /api/dashboard/recent-conversations
Get recent conversations for sidebar.

**Query Parameters:**
- `limit` (optional, default: 10): Number of conversations

**Response:**
```json
[
  {
    "name": "John Doe",
    "last_message_snippet": "Interested in the penthouse...",
    "minutes_ago": 15,
    "channel": "chat"
  }
]
```

**Behavior:**
- Distinct `external_thread_id` from last 60 minutes
- Only connected channels
- Organization-scoped

---

## Webhook Inbound Email (Postmark)

### POST /webhook/postmark/inbound
Handle inbound email from Postmark.

**Headers:**
- `X-Postmark-Signature`: Postmark signature

**Body:** Postmark inbound webhook format

**Behavior:**
- Verifies Postmark signature
- Creates `LeadMessage` with `channel='email'`
- Extracts `external_thread_id` from email headers
- Creates or resolves Lead by sender email
- If lead created, links `first_message_id`
- Emits `JobTask` if sequence step needed (`kind=email_sequence_step`)

**Response:**
```json
{
  "status": "success",
  "message_id": "uuid",
  "lead_id": "uuid"
}
```

---

## Dashboard Metrics Definitions

### Leads Today
- Count of `Lead` objects created today (org-scoped)
- Only includes leads from connected channels
- Delta: vs yesterday count

### Active Conversations
- Distinct `external_thread_id` in `LeadMessage` last 60 minutes
- Only connected channels
- Organization-scoped

### Inventory Value
- Sum of `Property.list_price` for active/published properties
- Organization-scoped
- Format: Currency (e.g., "$2.4M")

### Conversion Rate
- Formula: `converted_in_window / leads_created_in_window * 100`
- Window: Based on selected range (7d/30d/90d)
- Organization-scoped

---

## Channel Connection Status

### Model: ChannelConnection
- `organization`: FK to Organization
- `channel`: `facebook|instagram|email_inbound|chat`
- `status`: `connected|not_connected|error|pending`
- `connected_at`: DateTime (nullable)
- `error_message`: Text (nullable)
- `settings`: JSON field

### Defaults
- `chat` channel defaults to `connected` for every org
- Other channels start as `not_connected`

---

## Property Linking

### Model: LeadPropertyLink
- `organization`: FK
- `lead`: FK to Lead
- `property`: FK to Property
- `confidence`: Float (0.0-1.0)
- `evidence`: Text

### Resolution Order
1. Explicit payload keys (`property_id`/`slug`/URL) → confidence=1.0
2. URL/slug regex from text → confidence ≥0.9
3. MLS/ref code lookup → confidence ≥0.85
4. Fuzzy title/neighborhood + price proximity → confidence 0.6-0.8
5. Vector search over property embeddings → confidence ≥0.78 (configurable)

---

## Database Indexes

### Performance Indexes
- `Lead(organization_id, created_at)`
- `LeadMessage(organization_id, created_at)`
- `LeadMessage(organization_id, external_thread_id, created_at)`
- `Property(organization_id, status)`
- `JobTask(status, next_attempt_at)`
- `JobTask(organization_id, created_at)`
- `JobTask(lease_id)`

---

## Lease TTL
- Default lease duration: 10 minutes
- Jobs leased longer than TTL are automatically released
- n8n should complete jobs within lease window or release explicitly

