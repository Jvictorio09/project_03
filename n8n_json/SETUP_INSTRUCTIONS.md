# n8n Workflow Setup Instructions

## Fix for "The resource you are requesting could not be found" Error

This error typically occurs when n8n can't find the credentials resource referenced in the node. The updated `properties_modern.json` file fixes this by using header parameters directly instead of relying on credentials.

## Authentication Setup

The workflow uses **Bearer token authentication** via the `Authorization` header. You need to set up your N8N_TOKEN in n8n's environment variables.

### Option 1: Using n8n Environment Variables (Recommended)

1. In your n8n instance, go to **Settings** → **Environment Variables**
2. Add a new variable:
   - **Name**: `N8N_TOKEN`
   - **Value**: Your actual token from Django settings (`settings.N8N_TOKEN`)
3. Optionally add:
   - **Name**: `DJANGO_BASE_URL`
   - **Value**: `https://project03-production.up.railway.app` (or your Django URL)

### Option 2: Update the Workflow Directly

If you prefer not to use environment variables, you can edit the "Poll Jobs" node:

1. Open the workflow in n8n
2. Click on the **"Poll Jobs"** node
3. In the **Header Parameters** section, find the `Authorization` header
4. Replace `$env.N8N_TOKEN` with your actual token:
   ```
   Bearer YOUR_ACTUAL_TOKEN_HERE
   ```

### Getting Your N8N_TOKEN

Your Django application needs to have `N8N_TOKEN` configured in settings. Check your Django settings file or environment variables:

```python
# In Django settings.py or .env
N8N_TOKEN = "your-secret-token-here"
```

**Important**: This token must match what's configured in your Django application for the `/api/jobs/next/` endpoint.

## Verifying the Setup

1. **Import the workflow**: Import `properties_modern.json` into your n8n instance
2. **Set environment variables**: Add `N8N_TOKEN` (and optionally `DJANGO_BASE_URL`) to n8n
3. **Test the workflow**: 
   - Click "Execute Workflow" 
   - The "Poll Jobs" node should now make a successful API call

## Troubleshooting

### Error: "Invalid or missing token"
- **Cause**: The `N8N_TOKEN` doesn't match Django settings
- **Fix**: Verify the token in both n8n environment variables and Django settings

### Error: "The resource you are requesting could not be found"
- **Cause**: Old credentials configuration was referenced
- **Fix**: Use the updated `properties_modern.json` which uses header parameters directly

### Error: Connection timeout or connection refused
- **Cause**: The Django base URL is incorrect or unreachable
- **Fix**: 
  1. Verify `DJANGO_BASE_URL` is correct
  2. Check if the Django server is running
  3. Verify the endpoint `/api/jobs/next/` exists and is accessible

## Next Steps

After fixing the authentication:

1. **Test the workflow** - Execute it manually to verify all nodes work
2. **Set up scheduling** - Replace "Manual Trigger" with "Schedule Trigger" if you want automatic polling
3. **Monitor executions** - Check the execution logs to ensure jobs are being processed correctly

## Node Changes Summary

### Poll Jobs Node (Fixed)
- ✅ Removed credentials dependency
- ✅ Using header parameters directly
- ✅ Bearer token authentication via `Authorization` header
- ✅ Environment variable support for token

### Other Nodes
- All other nodes remain unchanged
- The callback node already uses header parameters correctly

