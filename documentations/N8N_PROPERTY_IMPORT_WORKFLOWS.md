# N8N Workflow Documentation for Property Import & Processing

## 📝 SUMMARY OF CHANGES

### What Was Implemented (Django Side)

1. **Jobs API** (`myApp/views_jobs.py`)
   - Created `GET /api/jobs/next/` endpoint for polling jobs
   - Created `POST /api/jobs/<uuid>/callback/` endpoint for callbacks
   - Implemented Bearer token authentication
   - Implemented HMAC signature verification
   - **Jobs are automatically leased when polled** (status changes to `in_progress`)

2. **Callback Handler** (`myApp/views_jobs.py` lines 186-275)
   - Processes `property_ai_enrichment` results
   - Processes `property_validation_deep` results  
   - **Automatically creates Property objects** when enrichment is complete
   - Updates PropertyUpload records with enrichment data

3. **CSV Import Integration** (`myApp/views_properties_import.py`)
   - Creates JobTask records for each CSV row imported
   - Job kind: `property_ai_enrichment`
   - Payload structure: `{upload_id, source, row_index}`

4. **URL Routes** (`myApp/urls.py` lines 130-132)
   - `/api/jobs/next/` → `jobs_next`
   - `/api/jobs/<uuid>/` → `job_update` (PATCH/POST)
   - `/api/jobs/<uuid>/callback/` → `job_update` (POST with HMAC)

### What Needs to be Done (n8n Side)

1. **Receive Credentials**: Get `N8N_TOKEN` and `N8N_HMAC_SECRET` from Django developer
2. **Configure Environment Variables**: Store N8N_TOKEN, N8N_HMAC_SECRET, DJANGO_BASE_URL in n8n
3. **Create Workflow**: Property AI Enrichment Poller
4. **Implement HMAC Signature**: For callback authentication
5. **Test Workflow**: Verify authentication and callback processing

**🔑 Security Note**: 
- Django **generates/provides** `N8N_TOKEN` and `N8N_HMAC_SECRET`
- n8n **receives/stores** these values to authenticate with Django
- These values must be kept secret and match exactly between Django and n8n

---

## 🎯 QUICK START FOR N8N DEVELOPER

This document provides everything the n8n developer needs to set up workflows for processing property import jobs. **Read this section first**, then refer to detailed sections below.

---

## 📋 CURRENT IMPLEMENTATION STATUS

### ✅ What's Already Implemented in Django

1. **JobTask Model** (`myApp/models.py`)
   - Status: `pending`, `in_progress`, `succeeded`, `failed`
   - Fields: `id`, `kind`, `payload`, `status`, `lease_id`, `attempts`, `next_attempt_at`
   - Job types: `property_ai_enrichment`, `property_validation_deep`

2. **Jobs API Endpoints** (`myApp/views_jobs.py`)
   - ✅ `GET /api/jobs/next/` - Poll for jobs (returns array)
   - ✅ `POST /api/jobs/<uuid>/callback/` - Callback with results
   - ✅ Authentication: Bearer token
   - ✅ HMAC signature verification for callbacks

3. **Callback Handler** (`myApp/views_jobs.py` line 186-275)
   - ✅ Processes `property_ai_enrichment` results
   - ✅ Processes `property_validation_deep` results
   - ✅ Auto-creates Property objects when complete
   - ✅ Updates PropertyUpload records

4. **CSV Import** (`myApp/views_properties_import.py`)
   - ✅ Creates JobTasks for each imported property
   - ✅ Job kind: `property_ai_enrichment`
   - ✅ Payload includes: `upload_id`, `source`, `row_index`

### ⚠️ What Needs to be Set Up in n8n

1. **Workflow 1**: Property AI Enrichment Poller
2. **Workflow 2**: Property Validation Deep Poller (optional)
3. **Environment Variables**: N8N_TOKEN, N8N_HMAC_SECRET, DJANGO_BASE_URL
4. **HMAC Signature Generation**: For callbacks

---

## 🔐 GENERATING CREDENTIALS (Django Developer)

### How to Generate N8N_TOKEN and N8N_HMAC_SECRET

**Option 1: Using Python Script**

Run the included script:
```bash
python generate_n8n_credentials.py
```

This will output:
```
N8N_TOKEN=abc123xyz...
N8N_HMAC_SECRET=def456uvw...
```

**Option 2: Using Python Command**

```bash
python -c "import secrets; print('N8N_TOKEN=' + secrets.token_urlsafe(32)); print('N8N_HMAC_SECRET=' + secrets.token_urlsafe(32))"
```

**Option 3: Using Django Management Command**

```bash
python manage.py shell
```

Then in Python shell:
```python
import secrets

# Generate N8N_TOKEN (Bearer token for authentication)
n8n_token = secrets.token_urlsafe(32)
print(f"N8N_TOKEN={n8n_token}")

# Generate N8N_HMAC_SECRET (HMAC signing secret)
n8n_hmac_secret = secrets.token_urlsafe(32)
print(f"N8N_HMAC_SECRET={n8n_hmac_secret}")
```

### After Generating Credentials

1. **Add to Django `.env` file**:
```bash
N8N_TOKEN=your-generated-token-here
N8N_HMAC_SECRET=your-generated-secret-here
```

2. **Share with n8n developer** via secure channel (not in code, not in git)

3. **Verify Django settings** (`myProject/settings.py`):
```python
N8N_TOKEN = os.getenv('N8N_TOKEN', '')
N8N_HMAC_SECRET = os.getenv('N8N_HMAC_SECRET', '')
```

4. **Restart Django server** to load new environment variables

**⚠️ Security Best Practices**:
- Generate unique values for each environment (dev/staging/production)
- Never commit these values to version control
- Use a password manager or secure secret management tool
- Rotate these credentials periodically (every 90 days recommended)

---

## 🔧 SETUP INSTRUCTIONS FOR N8N DEVELOPER

### Step 1: Configure Environment Variables in n8n

**🔑 WHO PROVIDES THESE VALUES?**

**Django provides these values** → n8n receives and stores them.

1. **Django developer sets** `N8N_TOKEN` and `N8N_HMAC_SECRET` in Django's environment variables
2. **Django uses these** to verify authentication and signatures from n8n
3. **n8n developer receives** these same values from Django developer
4. **n8n stores** them in n8n's environment variables to use when calling Django

**Process**:
```
Django Developer:
  1. Generates/sets N8N_TOKEN in Django .env file
  2. Generates/sets N8N_HMAC_SECRET in Django .env file
  3. Shares these values with n8n developer

n8n Developer:
  1. Receives N8N_TOKEN and N8N_HMAC_SECRET from Django developer
  2. Adds them to n8n environment variables
  3. Uses N8N_TOKEN as Bearer token in Authorization header
  4. Uses N8N_HMAC_SECRET to calculate HMAC signatures
```

**🌐 LOCAL DEVELOPMENT vs PRODUCTION**

For **local development**, use:
```bash
DJANGO_BASE_URL=http://localhost:8000
```

For **production**, use:
```bash
DJANGO_BASE_URL=https://your-domain.com
```

**⚠️ Local Development Setup**:
- Make sure Django server is running: `python manage.py runserver`
- Django typically runs on `http://localhost:8000` by default
- If n8n is running locally, it can call `http://localhost:8000`
- If n8n is running remotely (cloud/server), you'll need to use a tunnel (ngrok, etc.)

Add these to your n8n environment variables (Settings → Environment Variables):

```bash
# Required: Authentication token (provided by Django developer)
# This is the Bearer token Django expects in Authorization header
N8N_TOKEN=<value-from-django-developer>

# Required: HMAC secret (provided by Django developer)
# This string is used to sign callback requests
N8N_HMAC_SECRET=<value-from-django-developer>

# Required: Base URL of Django application
# FOR LOCAL DEVELOPMENT:
DJANGO_BASE_URL=http://localhost:8000

# FOR PRODUCTION (change this when deploying):
# DJANGO_BASE_URL=https://your-domain.com

# Optional: OpenAI API key (if n8n needs to call OpenAI directly)
OPENAI_API_KEY=sk-your-openai-key-here
```

**⚠️ IMPORTANT**: 
- **These values MUST match exactly** what Django has configured
- Django developer will provide these values to you
- Django verifies these values when receiving requests from n8n:
  - `N8N_TOKEN` → Used to verify `Authorization: Bearer <token>` header
  - `N8N_HMAC_SECRET` → Used to verify `X-Signature` header in callbacks
- These are secret values - don't commit them to version control
- In Django, these are read from environment variables `N8N_TOKEN` and `N8N_HMAC_SECRET` (see `myProject/settings.py` lines 264-265)

### Step 2: Test API Connection

Create a test workflow to verify authentication:

**Node 1: HTTP Request**
- Method: GET
- URL: `{{ $env.DJANGO_BASE_URL }}/api/jobs/next/`
  - **Local**: `http://localhost:8000/api/jobs/next/`
  - **Production**: `https://your-domain.com/api/jobs/next/`
- Headers:
  - `Authorization`: `Bearer {{ $env.N8N_TOKEN }}`

**Expected Response**:
- `200 OK` with empty array `[]` if no jobs
- `401 Unauthorized` if token is wrong
- `Connection refused` if Django server isn't running (local dev)

### Step 3: Create Property AI Enrichment Workflow

See detailed workflow steps below in "Workflow 1: Property AI Enrichment Poller"

---

## 🌐 API ENDPOINTS REFERENCE

### Base URL

**For Local Development**:
```
http://localhost:8000
```

**For Production**:
```
https://your-domain.com
```

**Note**: Use `{{ $env.DJANGO_BASE_URL }}` in n8n workflows to switch between environments easily.

### Endpoint 1: Poll for Jobs

**URL**: `GET /api/jobs/next/`

**Full URLs**:
- **Local**: `http://localhost:8000/api/jobs/next/?kind=property_ai_enrichment&limit=10`
- **Production**: `https://your-domain.com/api/jobs/next/?kind=property_ai_enrichment&limit=10`

**Query Parameters**:
- `kind` (optional): Filter by job kind (e.g., `property_ai_enrichment`)
- `limit` (optional): Max jobs to return (default: 50, max: 200)

**Headers**:
```
Authorization: Bearer <N8N_TOKEN>
```

**Response** (200 OK):
```json
[
  {
    "id": "3c4f90fd-0aa4-4b22-a2fe-f84396899d5a",
    "kind": "property_ai_enrichment",
    "payload": {
      "upload_id": "fa7a839f-8319-444e-b920-425950374ccd",
      "source": "csv_import",
      "row_index": 0
    },
    "attempts": 0,
    "lease_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "created_at": "2025-10-29T12:00:00Z"
  }
]
```

**Response** (204 No Content): No jobs available

**Response** (401 Unauthorized):
```json
{
  "error": "Invalid or missing token"
}
```

---

### Endpoint 2: Callback with Results

**URL**: `POST /api/jobs/<job_id>/callback/`

**Full URLs**:
- **Local**: `http://localhost:8000/api/jobs/<job_id>/callback/`
- **Production**: `https://your-domain.com/api/jobs/<job_id>/callback/`

**Headers**:
```
Authorization: Bearer <N8N_TOKEN>
X-Signature: sha256=<hex_signature>
X-Timestamp: <unix_timestamp>
Content-Type: application/json
```

**Request Body**:
```json
{
  "status": "succeeded",
  "lease_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "result": {
    "enhanced_description": "This modern 2BR condo offers stunning city views...",
    "property_features": ["Swimming pool", "Gym", "24/7 Security"],
    "property_type": "condo",
    "nearby_amenities": ["Shopping mall", "Public transport"],
    "selling_points": ["City views", "Modern amenities"]
  },
  "error": null
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "job_id": "3c4f90fd-0aa4-4b22-a2fe-f84396899d5a",
  "upload_id": "fa7a839f-8319-444e-b920-425950374ccd",
  "property_id": "new-property-uuid-if-created"
}
```

**Response** (401 Unauthorized):
```json
{
  "error": "Invalid HMAC signature"
}
```

---

## 🔐 HMAC SIGNATURE CALCULATION

**CRITICAL**: The callback endpoint requires HMAC signature verification.

### Signature Format

```
Message: {timestamp}.{request_body}
Algorithm: SHA256
Secret: N8N_HMAC_SECRET
Header Format: sha256={hex_signature}
```

### JavaScript Code for n8n

```javascript
const crypto = require('crypto');

// Get current Unix timestamp
const timestamp = Math.floor(Date.now() / 1000).toString();

// Prepare callback payload
const callbackPayload = {
  status: "succeeded",
  lease_id: "{{ $json.lease_id }}",  // From job polling response
  result: {
    enhanced_description: "{{ $json.enhanced_description }}",
    property_features: {{ $json.property_features }},
    property_type: "{{ $json.property_type }}",
    nearby_amenities: {{ $json.nearby_amenities }},
    selling_points: {{ $json.selling_points }}
  },
  error: null
};

// Convert payload to JSON string (MUST match exactly what you send)
const payloadStr = JSON.stringify(callbackPayload);

// Create message: timestamp + payload
const message = `${timestamp}.${payloadStr}`;

// Calculate HMAC signature
const secret = $env.N8N_HMAC_SECRET;
const signature = crypto
  .createHmac('sha256', secret)
  .update(message)
  .digest('hex');

// Return signature with prefix
return {
  signature: `sha256=${signature}`,
  timestamp: timestamp,
  payload: callbackPayload
};
```

### Example

```javascript
// Input:
timestamp = "1698580800"
payload = '{"status":"succeeded","lease_id":"abc123","result":{...}}'

// Message:
message = "1698580800.{\"status\":\"succeeded\",\"lease_id\":\"abc123\",\"result\":{...}}"

// Signature:
signature = crypto.createHmac('sha256', secret).update(message).digest('hex')
// Result: "sha256=a1b2c3d4e5f6..."
```

---

## 📦 PAYLOAD STRUCTURES

### Job Type: `property_ai_enrichment`

**Job Payload** (from polling):
```json
{
  "upload_id": "uuid",
  "source": "csv_import|manual|ai_text",
  "row_index": 0
}
```

**Callback Result** (to send):
```json
{
  "enhanced_description": "Detailed property description...",
  "property_features": ["Feature 1", "Feature 2"],
  "property_type": "condo|house|townhouse",
  "nearby_amenities": ["Amenity 1", "Amenity 2"],
  "selling_points": ["Point 1", "Point 2"]
}
```

**All fields are optional**, but send at least `enhanced_description` for best results.

---

### Job Type: `property_validation_deep`

**Job Payload** (from polling):
```json
{
  "upload_id": "uuid"
}
```

**Callback Result** (to send):
```json
{
  "validation_result": {
    "property_identification": "complete|partial|missing",
    "location_details": "complete|partial|missing",
    "lot_building": "complete|partial|missing",
    "interior_features": "complete|partial|missing",
    "property_features": "complete|partial|missing",
    "financial_info": "complete|partial|missing",
    "legal_info": "complete|partial|missing",
    "media_assets": "complete|partial|missing",
    "documentation": "complete|partial|missing"
  },
  "missing_fields": ["Field Name 1", "Field Name 2"],
  "completion_score": 0.85
}
```

---

## 🧪 TESTING PROCEDURE

### Test 1: Authentication

```bash
# Test with curl (Local Development)
curl -X GET "http://localhost:8000/api/jobs/next/" \
  -H "Authorization: Bearer YOUR_N8N_TOKEN"

# Test with curl (Production)
curl -X GET "https://your-domain.com/api/jobs/next/" \
  -H "Authorization: Bearer YOUR_N8N_TOKEN"

# Expected: 200 OK with empty array []
```

### Test 2: Create Test JobTask

Ask Django developer to create a test job:

```python
# In Django shell: python manage.py shell
from myApp.models import JobTask, Organization
import uuid

org = Organization.objects.first()
JobTask.objects.create(
    organization=org,
    kind='property_ai_enrichment',
    payload={
        'upload_id': 'test-upload-id',
        'source': 'manual',
        'row_index': 0
    },
    status='pending'
)
```

### Test 3: Poll for Job

```bash
# Local Development
curl -X GET "http://localhost:8000/api/jobs/next/?kind=property_ai_enrichment" \
  -H "Authorization: Bearer YOUR_N8N_TOKEN"

# Production
curl -X GET "https://your-domain.com/api/jobs/next/?kind=property_ai_enrichment" \
  -H "Authorization: Bearer YOUR_N8N_TOKEN"

# Expected: 200 OK with array containing your test job
```

### Test 4: Send Callback

```bash
# Local Development
curl -X POST "http://localhost:8000/api/jobs/<job_id>/callback/" \
  -H "Authorization: Bearer YOUR_N8N_TOKEN" \
  -H "X-Signature: sha256=<calculated_signature>" \
  -H "X-Timestamp: <unix_timestamp>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "succeeded",
    "lease_id": "<lease_id_from_polling>",
    "result": {
      "enhanced_description": "Test description",
      "property_features": ["Test feature"]
    },
    "error": null
  }'

# Production (same but with https://your-domain.com)

# Expected: 200 OK with success response
```

---

## 🏠 LOCAL DEVELOPMENT SETUP

### Prerequisites

1. **Django server running locally**:
   ```bash
   cd project_03
   python manage.py runserver
   ```
   Django should be accessible at `http://localhost:8000`

2. **n8n running** (local or cloud):
   - If n8n is running locally, it can directly call `http://localhost:8000`
   - If n8n is running remotely (cloud/server), you'll need:
     - **Option A**: Use ngrok/tunnel to expose localhost
     - **Option B**: Deploy Django to a staging server first

### Using ngrok for Remote n8n Access

If your n8n instance is in the cloud but Django is running locally:

1. **Install ngrok**: https://ngrok.com/download

2. **Expose Django port**:
   ```bash
   ngrok http 8000
   ```

3. **Copy the ngrok URL** (e.g., `https://abc123.ngrok.io`)

4. **Set in n8n**:
   ```bash
   DJANGO_BASE_URL=https://abc123.ngrok.io
   ```

**⚠️ Note**: ngrok URLs change each time you restart ngrok (unless you have a paid plan with fixed domains).

### Testing Locally

1. **Start Django server**:
   ```bash
   python manage.py runserver
   ```

2. **Verify Django is accessible**:
   ```bash
   curl http://localhost:8000/api/jobs/next/ \
     -H "Authorization: Bearer YOUR_N8N_TOKEN"
   ```

3. **Create test job** (in Django shell):
   ```python
   python manage.py shell
   ```
   ```python
   from myApp.models import JobTask, Organization
   org = Organization.objects.first()
   JobTask.objects.create(
       organization=org,
       kind='property_ai_enrichment',
       payload={'upload_id': 'test-123', 'source': 'manual'},
       status='pending'
   )
   ```

4. **Test n8n workflow** polls and processes it

### Environment Variable Setup (Local)

```bash
# In n8n environment variables:
DJANGO_BASE_URL=http://localhost:8000
N8N_TOKEN=<from-django-developer>
N8N_HMAC_SECRET=<from-django-developer>
```

---

## ⚠️ COMMON ISSUES & TROUBLESHOOTING

### Issue 1: "Invalid or missing token" (401)

**Cause**: N8N_TOKEN mismatch or missing Authorization header

**Fix**:
- Verify `N8N_TOKEN` in n8n matches Django `settings.N8N_TOKEN`
- Check Authorization header format: `Bearer <token>` (note the space)

### Issue 2: "Invalid HMAC signature" (401)

**Cause**: Signature calculation error or timestamp mismatch

**Fix**:
- Verify `N8N_HMAC_SECRET` matches Django settings
- Check message format: `{timestamp}.{json_body}` (note the dot)
- Ensure timestamp is within 5 minutes of current time
- Verify JSON stringification matches exactly (no extra spaces)

### Issue 3: "Lease ID mismatch" (409)

**Cause**: Using wrong `lease_id` from polling response

**Fix**:
- Use the `lease_id` from the job polling response
- Don't generate your own lease_id
- Ensure you're using the same job `id` and `lease_id` together

### Issue 4: "Job not found" (404)

**Cause**: Job ID doesn't exist or already processed

**Fix**:
- Verify job ID from polling response
- Check if job was already completed by another worker
- Check Django logs for job status

### Issue 6: "Connection refused" or "Cannot connect" (Local Dev)

**Cause**: Django server not running or wrong URL

**Fix**:
- Verify Django server is running: `python manage.py runserver`
- Check Django is accessible: `curl http://localhost:8000/health/`
- Verify `DJANGO_BASE_URL` in n8n: Should be `http://localhost:8000` for local dev
- If n8n is remote, use ngrok or deploy Django to staging

### Issue 7: CORS errors (Local Dev)

**Cause**: Django CORS settings blocking n8n requests

**Fix**:
- Django should allow localhost requests by default
- If using Django CORS middleware, ensure `localhost` is in allowed origins
- Check `myProject/settings.py` for CORS settings

---

## 📊 MONITORING & LOGGING

### Django Logs to Monitor

Check Django logs for:
- JobTask creation
- Callback reception
- Property creation
- Errors

**Log Locations**:
- Application logs: `logs/app.log`
- Django logs: Console output

### n8n Workflow Execution Logs

Monitor n8n workflow executions for:
- Polling frequency
- API response times
- Error rates
- HMAC signature failures

---

## 🔄 WORKFLOW EXAMPLES

See detailed workflow steps in sections below.

---

## Overview

This document describes the n8n workflows required to process property import jobs asynchronously. The Django application creates `JobTask` records that n8n polls and processes, then callbacks to Django with results.

## Architecture

```
Django App (creates JobTask)
    ↓
JobTask (status: 'pending')
    ↓
n8n Workflow (polls every 30s)
    ↓
n8n Processing (AI enrichment, validation)
    ↓
n8n Callback (POST /api/jobs/<uuid>/callback/)
    ↓
Django App (updates PropertyUpload, creates Property)
```

---

## Jobs API Endpoints

### GET `/api/jobs/next/`

**Purpose**: Poll for the next available job to process

**Authentication**: Bearer token in `Authorization` header
```
Authorization: Bearer <N8N_TOKEN>
```

**Response** (200 OK - Array of jobs):
```json
[
  {
    "id": "uuid",
    "kind": "property_ai_enrichment",
    "payload": {
      "upload_id": "uuid",
      "source": "csv_import",
      "row_index": 0
    },
    "attempts": 0,
    "lease_id": "uuid",
    "created_at": "2025-10-29T12:00:00Z"
  },
  {
    "id": "uuid",
    "kind": "property_validation_deep",
    "payload": {
      "upload_id": "uuid"
    },
    "attempts": 0,
    "lease_id": "uuid",
    "created_at": "2025-10-29T12:00:00Z"
  }
]
```

**Note**: The endpoint returns an array of jobs (up to 50 by default). Process each job in the array.

**Response** (204 No Content): No jobs available

**Error Response** (401):
```json
{
  "error": "Invalid token"
}
```

---

### PATCH/POST `/api/jobs/<uuid>/`

**Purpose**: Update job status and lease information

**Authentication**: Bearer token

**Request Body**:
```json
{
  "status": "in_progress",
  "lease_id": "uuid",
  "attempts": 1
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "job_id": "uuid",
  "status": "in_progress"
}
```

---

### POST `/api/jobs/<uuid>/callback/`

**Purpose**: Callback endpoint for job completion

**Authentication**: HMAC signature verification

**Headers**:
```
X-Signature: sha256=<hex_signature>
X-Timestamp: <unix_timestamp>
Authorization: Bearer <N8N_TOKEN>
```

**Request Body**:
```json
{
  "status": "succeeded",
  "lease_id": "uuid",
  "result": {
    "enhanced_description": "...",
    "property_features": ["..."],
    "property_type": "condo",
    "nearby_amenities": ["..."],
    "selling_points": ["..."]
  },
  "error": null
}
```

**Note**: `lease_id` is required and must match the lease_id from the polling response.

**Response** (200 OK):
```json
{
  "success": true,
  "job_id": "uuid",
  "upload_id": "uuid",
  "property_id": "uuid",
  "message": "Property created successfully"
}
```

---

## Workflow 1: Property AI Enrichment Poller

### Purpose
Poll for `property_ai_enrichment` jobs and process them with AI to enrich property details.

### Trigger
**Schedule Trigger**: Every 30 seconds

### Workflow Steps

#### Step 1: Poll for Next Jobs
- **Node Type**: HTTP Request
- **Method**: GET
- **URL**: `{{ $env.DJANGO_BASE_URL }}/api/jobs/next/?kind=property_ai_enrichment`
  - **Local Development**: `http://localhost:8000/api/jobs/next/?kind=property_ai_enrichment`
  - **Production**: `https://your-domain.com/api/jobs/next/?kind=property_ai_enrichment`
- **Query Parameters**:
  - `kind` (optional): Filter by job kind (e.g., `property_ai_enrichment`)
  - `limit` (optional): Max jobs to return (default: 50, max: 200)
- **Headers**:
  ```
  Authorization: Bearer {{ $env.N8N_TOKEN }}
  ```
- **Response Handling**: 
  - If `204 No Content`: Stop workflow (no jobs)
  - If `200 OK`: Returns array of jobs → Continue to Step 2

#### Step 2: Split Jobs Array
- **Node Type**: Split in Batches
- **Batch Size**: 1 (process one job at a time)
- **Or use**: Loop Over Items node

#### Step 3: Extract Job Details
- **Node Type**: Code (JavaScript)
- **Code**:
```javascript
const job = $input.item.json;
return {
  jobId: job.id,
  kind: job.kind,
  uploadId: job.payload.upload_id,
  leaseId: job.lease_id,
  payload: job.payload
};
```

#### Step 4: Fetch PropertyUpload Data

**⚠️ IMPORTANT**: The PropertyUpload data isn't directly accessible via a public API endpoint yet. You have two options:

**Option A: Use JobTask Payload (Recommended)**
- The PropertyUpload data should be included in the JobTask payload when created
- For now, you'll need to work with the `upload_id` only
- Contact Django developer to add PropertyUpload data to JobTask payload if needed

**Option B: Create API Endpoint (If Needed)**
- Django developer can create `GET /api/property-uploads/<uuid>/` endpoint
- This would return PropertyUpload data including: title, description, price, city, area, beds, baths

**Option C: Use OpenAI with Minimal Data**
- For AI enrichment, you can work with just the `upload_id` 
- The AI prompt can generate enrichment based on minimal context
- Django callback handler will merge enrichment with existing PropertyUpload data

**Current Workaround**: Since we don't have direct PropertyUpload access, the n8n workflow should:
1. Use OpenAI to generate generic enrichment based on property type assumptions
2. Django callback handler will merge enrichment with actual PropertyUpload data

**Example Workflow Without PropertyUpload Data**:
```javascript
// In n8n Code node
const job = $input.item.json;
// We have upload_id but not property data
// Generate enrichment based on property type assumptions
return {
  uploadId: job.payload.upload_id,
  source: job.payload.source, // csv_import, manual, ai_text
  // AI will generate enrichment based on context
};
```

For now, proceed with AI enrichment using minimal context from the job payload.

#### Step 5: AI Enrichment
- **Node Type**: OpenAI
- **Model**: `gpt-4`
- **System Prompt**:
```
You are a real estate data enrichment assistant. Given property information, generate additional details that would be valuable for a property listing.

Current Property Information:
- Title: {{ $json.title }}
- Description: {{ $json.description }}
- Price: ${{ $json.price_amount }}
- City: {{ $json.city }}
- Area: {{ $json.area }}
- Bedrooms: {{ $json.beds }}
- Bathrooms: {{ $json.baths }}

Please enrich this property listing by:
1. Improving the description if it's generic or short (make it appealing and detailed)
2. Adding property features (amenities, facilities, nearby attractions)
3. Suggesting property type if not clear
4. Adding any missing details that would help buyers/renters

Return ONLY a valid JSON object with these fields:
{
    "enhanced_description": "detailed, appealing property description",
    "property_features": ["feature1", "feature2", "feature3"],
    "property_type": "condo/house/townhouse/etc",
    "nearby_amenities": ["amenity1", "amenity2"],
    "selling_points": ["point1", "point2"]
}

Return ONLY valid JSON, no markdown code blocks.
```

- **User Prompt**: Same as system prompt (or just property data)
- **Temperature**: 0.7
- **Max Tokens**: 800

#### Step 6: Parse AI Response
- **Node Type**: Code (JavaScript)
- **Code**:
```javascript
const aiResponse = $input.item.json.choices[0].message.content;
let jsonStr = aiResponse.trim();

// Remove markdown code blocks if present
if (jsonStr.startsWith('```')) {
  jsonStr = jsonStr.split('```')[1];
  if (jsonStr.startsWith('json')) {
    jsonStr = jsonStr.substring(4);
  }
  jsonStr = jsonStr.trim();
}

try {
  return JSON.parse(jsonStr);
} catch (e) {
  return {
    error: `Failed to parse AI response: ${e.message}`,
    raw_response: aiResponse
  };
}
```

#### Step 7: Calculate HMAC Signature
- **Node Type**: Code (JavaScript)
- **Code**:
```javascript
const crypto = require('crypto');
const timestamp = Math.floor(Date.now() / 1000).toString();
const secret = $env.N8N_HMAC_SECRET;

// Prepare callback payload
const callbackPayload = {
  status: "succeeded",
  result: $json, // From AI enrichment (parsed JSON)
  error: null,
  lease_id: $('Step 3').item.json.leaseId  // From extracted job details
};

const payloadStr = JSON.stringify(callbackPayload);
const message = `${timestamp}.${payloadStr}`;
const signature = crypto
  .createHmac('sha256', secret)
  .update(message)
  .digest('hex');

return {
  signature: `sha256=${signature}`,
  timestamp: timestamp,
  payload: callbackPayload
};
```

#### Step 8: Callback to Django
- **Node Type**: HTTP Request
- **Method**: POST
- **URL**: `{{ $env.DJANGO_BASE_URL }}/api/jobs/{{ $('Step 3').item.json.jobId }}/callback/`
  - **Local Development**: `http://localhost:8000/api/jobs/<job_id>/callback/`
  - **Production**: `https://your-domain.com/api/jobs/<job_id>/callback/`
- **Headers**:
  ```
  Authorization: Bearer {{ $env.N8N_TOKEN }}
  X-Signature: {{ $json.signature }}
  X-Timestamp: {{ $json.timestamp }}
  Content-Type: application/json
  ```
- **Body**: `{{ JSON.stringify($json.payload) }}`

#### Step 8: Error Handling
- **Node Type**: IF (Check if callback failed)
- **Conditions**: 
  - If callback status code != 200: Route to error handling
- **Error Handler**: 
  - Update job status to "failed"
  - Log error details
  - Optionally retry

---

## Workflow 2: Property Validation Deep Poller

### Purpose
Poll for `property_validation_deep` jobs and perform comprehensive validation against a checklist.

### Trigger
**Schedule Trigger**: Every 30 seconds (can run alongside enrichment workflow)

### Workflow Steps

#### Step 1-3: Same as Workflow 1 (Poll, Extract, Lease)

#### Step 4: Fetch PropertyUpload Data
- Same as Workflow 1, Step 4

#### Step 5: Deep Validation Check
- **Node Type**: OpenAI
- **Model**: `gpt-4`
- **System Prompt**:
```
You are a real estate data validator AI. You will receive property data and cross-check it against a comprehensive checklist.

For each section, determine whether the information is:
- ✅ Complete (enough data to answer related user queries confidently)
- ⚠️ Partial (some critical fields are missing)
- ❌ Missing (cannot answer questions reliably for that section)

COMPREHENSIVE REAL ESTATE CHECKLIST:

🏡 1. Property Identification
- MLS Number / Internal Property ID
- Property Title / Listing Name
- Property Type (Single Family, Condo, Townhouse, Multi-family, Commercial, Land)
- Subtype (e.g., Duplex, High-rise Condo, Manufactured Home)
- Listing Status (Active, Pending, Contingent, Sold, Off-market)
- Listing Date & Last Updated
- Listing Agent & Brokerage Information
- Days on Market (DOM)

📍 2. Location Details
- Full Street Address (House No., Street, City, State, ZIP)
- County / Census Tract
- Subdivision / Community Name
- HOA / Community Association (Y/N + name)
- School District (Elementary, Middle, High School zones)
- Nearby Landmarks & Transportation Access
- GPS Coordinates (Latitude, Longitude)

📐 3. Lot and Building Information
- Lot Size (sq ft or acres)
- Lot Dimensions
- Zoning Code & Land Use Type
- Year Built / Year Renovated
- Total Living Area (sq ft)
- Total Building Area
- Number of Stories
- Basement (Finished / Unfinished / Walkout)
- Roof Type & Material
- Exterior Construction Material
- Parking (Garage spaces, driveway capacity)

🛋 4. Interior Features
- Number of Bedrooms
- Number of Bathrooms (Full / Half)
- Kitchen features (appliances, countertops, layout)
- Flooring Materials
- HVAC (Heating, Cooling, Ventilation details)
- Fireplace (Y/N, type)
- Laundry Room (Location & Type)
- Accessibility Features
- Energy Efficiency Features

🏢 5. Property Features & Amenities
- Outdoor spaces (Deck, Patio, Balcony, Pool, Lawn, Fence)
- Landscaping / Irrigation systems
- HOA Amenities (Gym, Tennis courts, Clubhouse, Pool)
- Security systems / Gated community
- Views (Mountain, City, Water, Golf course, etc.)
- Waterfront / Water access details
- Inclusions / Exclusions

💰 6. Pricing and Financial Information
- List Price (USD)
- Price per sq ft
- HOA Fees (monthly/annual)
- Property Taxes (annual)
- Special Assessments
- Utility Costs
- Lease information (for rentals)
- Financing options offered
- Estimated Closing Costs

📜 7. Legal & Ownership Information
- Title Status (Fee Simple, Leasehold, Trust, REO, Foreclosure)
- Deed Type
- Parcel Number (APN)
- Recorded Liens / Encumbrances
- Easements / Rights of Way
- Occupancy Status
- Zoning Variances or Permits
- Flood Zone Classification

🖼 8. Media & Marketing Assets
- Professional Photos (min. cover + gallery)
- Floor Plans
- Virtual Tour / 3D Walkthrough
- Video Tours
- Drone Photography
- Property Website / Landing Page
- Marketing Remarks / Description

📎 9. Documentation & Disclosures
- Property Disclosure Statements
- Title Report
- HOA Documents
- Recent Inspection Reports
- Appraisal Report
- Survey / Plat Map
- Permits
- Energy Certifications

Property Data:
{{ property_data_json }}

Return a JSON object with this structure:
{
  "property_identification": "complete|partial|missing",
  "location_details": "complete|partial|missing",
  "lot_building": "complete|partial|missing",
  "interior_features": "complete|partial|missing",
  "property_features": "complete|partial|missing",
  "financial_info": "complete|partial|missing",
  "legal_info": "complete|partial|missing",
  "media_assets": "complete|partial|missing",
  "documentation": "complete|partial|missing",
  "missing_fields": ["Field Name 1", "Field Name 2"],
  "completion_score": 0.85
}
```

#### Step 6: Parse Validation Result
- Similar to Workflow 1, Step 6

#### Step 7: Callback to Django
- **Node Type**: HTTP Request
- **Method**: POST
- **URL**: `https://your-domain.com/api/jobs/{{ $('Step 2').item.json.jobId }}/callback/`
- **Body**:
```json
{
  "status": "succeeded",
  "result": {
    "validation_result": {
      "property_identification": "complete",
      "location_details": "partial",
      "lot_building": "missing",
      "interior_features": "complete",
      "property_features": "partial",
      "financial_info": "complete",
      "legal_info": "missing",
      "media_assets": "complete",
      "documentation": "missing"
    },
    "missing_fields": [
      "Full Street Address",
      "Lot Size",
      "Title Status"
    ],
    "completion_score": 0.65
  },
  "error": null
}
```

---

## Workflow 3: Batch Property Completion (Optional)

### Purpose
For CSV imports, process multiple PropertyUpload records and create Property objects in batch.

### Trigger
**Schedule Trigger**: Every 5 minutes

### Workflow Steps

#### Step 1: Query Completed PropertyUploads
- **Node Type**: HTTP Request
- **Method**: GET
- **URL**: `https://your-domain.com/api/property-uploads/completed/?limit=50`
- **Note**: This endpoint may need to be created

#### Step 2: Loop Through Each Upload
- **Node Type**: Split in Batches
- **Batch Size**: 10

#### Step 3: Create Property
- **Node Type**: HTTP Request
- **Method**: POST
- **URL**: `https://your-domain.com/api/property-uploads/{{ $json.upload_id }}/create-property/`
- **Note**: This endpoint may need to be created

---

## Environment Variables Required

Add these to your n8n environment:

```bash
N8N_TOKEN=your-secret-token-here
N8N_HMAC_SECRET=your-hmac-secret-key-here
DJANGO_BASE_URL=https://your-domain.com
OPENAI_API_KEY=your-openai-api-key
```

---

## Job Types Reference

### `property_ai_enrichment`
**Purpose**: Enrich PropertyUpload with AI-generated details

**Payload**:
```json
{
  "upload_id": "uuid",
  "source": "csv_import|manual|ai_text",
  "row_index": 0
}
```

**Expected Result**:
```json
{
  "enhanced_description": "...",
  "property_features": ["..."],
  "property_type": "condo",
  "nearby_amenities": ["..."],
  "selling_points": ["..."]
}
```

**Django Processing**:
- Updates PropertyUpload.description with enriched content
- Stores enrichment data in `ai_validation_result.ai_enrichment`
- Adds features to description
- If critical fields present, creates Property object

---

### `property_validation_deep`
**Purpose**: Perform comprehensive validation against checklist

**Payload**:
```json
{
  "upload_id": "uuid"
}
```

**Expected Result**:
```json
{
  "validation_result": {
    "property_identification": "complete|partial|missing",
    "location_details": "complete|partial|missing",
    "lot_building": "complete|partial|missing",
    "interior_features": "complete|partial|missing",
    "property_features": "complete|partial|missing",
    "financial_info": "complete|partial|missing",
    "legal_info": "complete|partial|missing",
    "media_assets": "complete|partial|missing",
    "documentation": "complete|partial|missing"
  },
  "missing_fields": ["Field 1", "Field 2"],
  "completion_score": 0.0-1.0
}
```

**Django Processing**:
- Updates PropertyUpload.ai_validation_result
- Updates PropertyUpload.missing_fields
- May trigger validation chat if critical fields missing

---

## Error Handling

### Workflow Errors

**If AI API fails**:
- Return error in callback:
```json
{
  "status": "failed",
  "error": "OpenAI API error: ...",
  "result": null
}
```

**If JobTask not found**:
- Return error in callback
- Django will handle gracefully

**If Lease conflicts**:
- Another worker already processing
- Skip job, continue to next

### Retry Logic

**n8n Retry Configuration**:
- Max retries: 3
- Retry delay: Exponential backoff (1s, 2s, 4s)
- Retry on: Network errors, 5xx errors

**JobTask Retry Handling**:
- Django tracks `attempts` field
- If `attempts < max_attempts`, job can be retried
- Set `next_attempt_at` for delayed retry

---

## Testing Workflows

### Test Job Creation

1. **Create test JobTask in Django**:
```python
from myApp.models import JobTask, Organization
import uuid

org = Organization.objects.first()
JobTask.objects.create(
    organization=org,
    kind='property_ai_enrichment',
    payload={
        'upload_id': 'test-upload-id',
        'source': 'manual',
        'row_index': 0
    },
    status='pending'
)
```

2. **Trigger n8n workflow** (or wait for schedule)

3. **Verify callback**:
- Check Django logs
- Check PropertyUpload.ai_validation_result
- Check Property object creation

### Test with Sample Data

**PropertyUpload Data**:
```json
{
  "title": "Test Property",
  "description": "A nice property",
  "price_amount": 3500,
  "city": "Makati",
  "area": "BGC",
  "beds": 2,
  "baths": 2
}
```

**Expected AI Enrichment**:
- Enhanced description with details
- Property features list
- Property type detection
- Nearby amenities
- Selling points

---

## Monitoring & Observability

### Key Metrics

**n8n Workflow Metrics**:
- Jobs processed per hour
- Average processing time
- Error rate by job type
- Callback success rate

**Django Metrics**:
- JobTask status distribution
- Average time from creation to completion
- Failed job count
- Retry rate

### Logging

**n8n Logs**:
- Log each workflow execution
- Log AI API calls
- Log callback responses
- Log errors with full context

**Django Logs**:
- JobTask creation
- Callback reception
- Property creation
- Errors

---

## Performance Optimization

### Batch Processing

For CSV imports with many properties:
- Process 5-10 properties in parallel
- Use n8n's "Split in Batches" node
- Limit concurrent OpenAI API calls

### Rate Limiting

**OpenAI API**:
- Monitor rate limits
- Implement exponential backoff
- Use queue for high-volume imports

**Django API**:
- Poll interval: 30 seconds (not too aggressive)
- Max concurrent leases: 10 per organization

---

## Troubleshooting

### Issue: Jobs not being picked up

**Check**:
- n8n workflow is active
- Schedule trigger is running
- N8N_TOKEN is correct
- JobTask.status is 'pending'

### Issue: HMAC signature verification fails

**Check**:
- N8N_HMAC_SECRET matches Django settings
- Timestamp is within 5 minutes
- Signature calculation is correct
- Payload matches exactly

### Issue: AI enrichment fails

**Check**:
- OpenAI API key is valid
- API rate limits not exceeded
- Response parsing handles markdown code blocks
- Error handling in n8n workflow

### Issue: Property not created after callback

**Check**:
- Callback returned success
- PropertyUpload has critical fields (title, price, city)
- No errors in Django logs
- PropertyUpload.status is 'complete'

---

## Example n8n Workflow JSON

### Basic Property AI Enrichment Workflow

```json
{
  "name": "Property AI Enrichment Poller",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [{"field": "seconds", "secondsInterval": 30}]
        }
      }
    },
    {
      "name": "Poll Jobs",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "={{ $env.DJANGO_BASE_URL }}/api/jobs/next/",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "=Bearer {{ $env.N8N_TOKEN }}"
            }
          ]
        }
      }
    },
    {
      "name": "Check Response",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{ $json.statusCode }}",
              "operation": "equal",
              "value2": 200
            }
          ]
        }
      }
    },
    {
      "name": "Lease Job",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "PATCH",
        "url": "={{ $env.DJANGO_BASE_URL }}/api/jobs/{{ $('Poll Jobs').item.json.job_id }}/",
        "headers": {
          "Authorization": "=Bearer {{ $env.N8N_TOKEN }}"
        },
        "bodyParameters": {
          "parameters": [
            {
              "name": "status",
              "value": "in_progress"
            },
            {
              "name": "lease_id",
              "value": "={{ $workflow.id }}"
            }
          ]
        }
      }
    },
    {
      "name": "AI Enrichment",
      "type": "n8n-nodes-base.openAi",
      "parameters": {
        "operation": "complete",
        "model": "gpt-4",
        "systemMessage": "You are a real estate data enrichment assistant...",
        "options": {
          "temperature": 0.7,
          "maxTokens": 800
        }
      }
    },
    {
      "name": "Parse Response",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Parse AI response JSON"
      }
    },
    {
      "name": "Calculate HMAC",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Calculate HMAC signature"
      }
    },
    {
      "name": "Callback",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "={{ $env.DJANGO_BASE_URL }}/api/jobs/{{ $('Poll Jobs').item.json.job_id }}/callback/",
        "headers": {
          "Authorization": "=Bearer {{ $env.N8N_TOKEN }}",
          "X-Signature": "={{ $json.signature }}",
          "X-Timestamp": "={{ $json.timestamp }}"
        },
        "bodyParameters": {
          "parameters": [
            {
              "name": "status",
              "value": "succeeded"
            },
            {
              "name": "result",
              "value": "={{ $json }}"
            }
          ]
        }
      }
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [[{"node": "Poll Jobs"}]]
    },
    "Poll Jobs": {
      "main": [[{"node": "Check Response"}]]
    },
    "Check Response": {
      "main": [
        [{"node": "Lease Job"}],
        []
      ]
    },
    "Lease Job": {
      "main": [[{"node": "AI Enrichment"}]]
    },
    "AI Enrichment": {
      "main": [[{"node": "Parse Response"}]]
    },
    "Parse Response": {
      "main": [[{"node": "Calculate HMAC"}]]
    },
    "Calculate HMAC": {
      "main": [[{"node": "Callback"}]]
    }
  }
}
```

---

## Django Callback Handler

The callback endpoint (`/api/jobs/<uuid>/callback/`) should:

1. **Verify HMAC signature**
2. **Load JobTask**
3. **Update PropertyUpload** with enrichment data
4. **Create Property** if validation complete
5. **Update JobTask status** to 'succeeded'
6. **Create JobEvent** record
7. **Return success response**

**Example Callback Handler**:
```python
# In views_jobs.py or views_webhook.py

def handle_property_ai_enrichment_callback(job: JobTask, result: dict):
    """Handle callback from n8n for property AI enrichment"""
    from .models import PropertyUpload
    
    upload_id = job.payload.get('upload_id')
    upload = PropertyUpload.objects.get(id=upload_id)
    
    # Update PropertyUpload with enrichment
    if result.get('enhanced_description'):
        if upload.description:
            upload.description = f"{upload.description}\n\n{result['enhanced_description']}"
        else:
            upload.description = result['enhanced_description']
    
    # Store enrichment data
    upload.ai_validation_result = {
        **upload.ai_validation_result,
        'ai_enrichment': result,
        'enriched_at': timezone.now().isoformat()
    }
    
    # Add features
    if result.get('property_features'):
        features_text = "\n\nFeatures:\n" + "\n".join([f"• {f}" for f in result['property_features'][:10]])
        upload.description += features_text
    
    upload.save()
    
    # Auto-complete if critical fields present
    if upload.title and upload.price_amount and upload.city:
        upload.status = 'complete'
        upload.save()
        # Create Property
        from .views_properties_import import create_property_from_upload
        property_obj = create_property_from_upload(upload)
        return {'property_id': str(property_obj.id)}
    
    return {'upload_id': str(upload.id)}
```

---

## Summary

**Required n8n Workflows**:

1. **Property AI Enrichment Poller** (every 30s)
   - Polls `/api/jobs/next/`
   - Processes `property_ai_enrichment` jobs
   - Calls OpenAI for enrichment
   - Callbacks with results

2. **Property Validation Deep Poller** (every 30s, optional)
   - Polls `/api/jobs/next/`
   - Processes `property_validation_deep` jobs
   - Performs comprehensive validation
   - Callbacks with validation results

**Key Points**:
- Use Bearer token authentication for polling
- Use HMAC signature for callbacks
- Handle errors gracefully
- Retry failed jobs
- Monitor processing times

This setup ensures reliable, scalable background processing of property imports with AI enrichment.

