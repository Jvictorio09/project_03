# N8N Workflows for KaTek Real Estate Platform

This directory contains all n8n workflow JSON files needed for the platform.

## 📋 Available Workflows

### 0. Test Connection (`0_test_connection.json`)
- **Purpose**: Test Django API connectivity and authentication
- **Trigger**: Manual
- **Use**: Verify your n8n setup is working before running production workflows

### 1. Property AI Enrichment (`1_property_ai_enrichment.json`)
- **Purpose**: Polls for property enrichment jobs and uses OpenAI to enhance property descriptions
- **Trigger**: Schedule (every 30 seconds)
- **Job Kind**: `property_ai_enrichment`
- **Features**: 
  - Polls Django API for pending jobs
  - Uses OpenAI GPT-4o-mini to enrich property data
  - Returns enhanced descriptions, features, amenities, selling points
  - HMAC-signed callbacks to Django

### 2. Property Validation Deep (`2_property_validation_deep.json`)
- **Purpose**: Deep validation of property data quality
- **Trigger**: Schedule (every 30 seconds)
- **Job Kind**: `property_validation_deep`
- **Features**:
  - Validates property data completeness
  - Identifies missing fields
  - Provides data quality scores
  - Returns recommendations

### 3. Properties (Legacy) (`properties.json`)
- **Purpose**: Manual trigger version of property enrichment
- **Trigger**: Manual
- **Note**: Use the scheduled version (`1_property_ai_enrichment.json`) for production

## 🔧 Setup Instructions

### Step 1: Configure Environment Variables in n8n

Go to **Settings → Environment Variables** in n8n and add:

```bash
# Required: Django authentication token (get from Django developer)
N8N_TOKEN=your-token-here

# Required: HMAC secret for signing callbacks (get from Django developer)
N8N_HMAC_SECRET=your-secret-here

# Required: Django base URL
# For local development with ngrok:
DJANGO_BASE_URL=http://your-ngrok-url.ngrok.io

# For production:
# DJANGO_BASE_URL=https://project03-production.up.railway.app
```

### Step 2: Configure Credentials in n8n

Create these credentials in n8n:

#### Django Header Token (FREE)
- **Type**: Header Auth
- **Name**: `Django – Header Token (FREE)`
- **Header Name**: `Authorization`
- **Header Value**: `Bearer {{ $env.N8N_TOKEN }}`

#### OpenAI API
- **Type**: OpenAI API
- **Name**: `OpenAI – Katalyst`
- **API Key**: Your OpenAI API key

### Step 3: Import Workflows

1. In n8n, go to **Workflows**
2. Click **Import from File**
3. Select the JSON file you want to import
4. Configure credentials when prompted
5. Activate the workflow

### Step 4: Update HMAC Secret

After importing, update the HMAC secret in the crypto node:
- Open the workflow
- Find the "Sign HMAC" node
- Set the secret to: `={{ $env.N8N_HMAC_SECRET }}`

## 📝 Workflow Details

### Property AI Enrichment Flow

```
Schedule Trigger (every 30s)
    ↓
Poll Jobs (GET /api/jobs/next/)
    ↓
Has Jobs? (Switch: 200/204)
    ↓
Extract Body → Split Jobs → Batches
    ↓
Pick Fields → Build Prompt
    ↓
OpenAI Enrich (GPT-4o-mini)
    ↓
Parse JSON → Build Callback
    ↓
Attach IDs → Sign HMAC
    ↓
Build Headers → Callback Django
    ↓
(loop back to batches)
```

### Authentication

All workflows use:
- **Bearer Token**: `Authorization: Bearer {{ $env.N8N_TOKEN }}`
- **HMAC Signatures**: For callback requests (X-Signature header)

## 🧪 Testing

### Test Polling Endpoint

Use the `0_test_connection.json` workflow to verify:
- Django API connectivity
- Authentication token validity
- Health endpoint status

**Expected Responses**:
- `200 OK` with `[]` → No jobs available (normal)
- `200 OK` with `[{...}]` → Jobs available
- `204 No Content` → No jobs (also normal)
- `401 Unauthorized` → Token mismatch

## 🔍 Troubleshooting

### "Connection Refused"
- **Cause**: Django server not running or wrong URL
- **Fix**: 
  - Verify Django is running: `python manage.py runserver`
  - Check `DJANGO_BASE_URL` matches your setup
  - If n8n is remote, use ngrok or deploy Django

### "Invalid Signature"
- **Cause**: HMAC secret mismatch
- **Fix**: Verify `N8N_HMAC_SECRET` matches Django settings

### "Invalid Token"
- **Cause**: N8N_TOKEN mismatch or missing Authorization header
- **Fix**: Check credentials configuration and token value

### No Jobs Processing
- **Cause**: No jobs in database or wrong `kind` parameter
- **Fix**: 
  - Verify jobs exist: Check Django admin or database
  - Verify job `kind` matches workflow query parameter

## 📚 Documentation

- **Full Documentation**: `documentations/N8N_PROPERTY_IMPORT_WORKFLOWS.md`
- **API Contracts**: `documentations/API_CONTRACTS_DASHBOARD.md`
- **Architecture**: `documentations/architecture/N8N_INTEGRATION_ARCHITECTURE.md`

## 🔐 Security Notes

- **Never commit** `N8N_TOKEN` or `N8N_HMAC_SECRET` to version control
- Use environment variables for all secrets
- Rotate credentials periodically (every 90 days recommended)
- Use HTTPS in production

## 🚀 Production Deployment

1. Deploy Django to production (Railway, Fly.io, etc.)
2. Set `DJANGO_BASE_URL` in n8n to production URL
3. Ensure Django has `N8N_TOKEN` and `N8N_HMAC_SECRET` set
4. Verify `ALLOWED_HOSTS` includes your domain
5. Activate workflows in n8n
6. Monitor execution logs

## 📞 Support

For issues:
1. Check n8n execution logs
2. Check Django logs (`logs/app.log`)
3. Verify environment variables
4. Test API endpoints manually
5. Contact Django developer for token/secret issues

