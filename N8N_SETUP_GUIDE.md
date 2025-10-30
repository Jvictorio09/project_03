# n8n Integration Setup Guide

## 🚀 Quick Start

### 1. Set Environment Variables

Add these to your `.env` file or environment:

```bash
# Enable n8n orchestration
USE_N8N_ORCHESTRATION=true

# Your n8n webhook URL (get this from n8n after importing workflows)
N8N_QUEUE_WEBHOOK_URL=https://your-n8n-instance.com/webhook/queue-campaign-send

# Shared secret for HMAC signatures
N8N_HMAC_SECRET=your-super-secret-key-here
```

### 2. Import n8n Workflows

1. **Workflow A**: Import `n8n_json/Workflow_A_Queue_Campaign_Send.json`
   - This handles the main campaign queuing and sending
   - Set webhook URL: `/webhook/queue-campaign-send`

2. **Workflow B**: Import `n8n_json/Workflow_B_Due_Messages_Sweep.json`
   - This runs every 2 minutes to catch missed messages
   - No webhook needed (cron trigger)

3. **Workflow C**: Import `n8n_json/Workflow_C_Property_Event_Campaigns.json`
   - This handles property-triggered campaigns
   - Set webhook URL: `/webhook/property-events`

### 3. Configure n8n Workflow Variables

In each workflow, set these variables:

- `djangoBaseUrl`: `http://localhost:8000` (or your Django URL)
- `n8nHmacSecret`: Same as `N8N_HMAC_SECRET` in Django
- `workflowAWebhookUrl`: The webhook URL for Workflow A

### 4. Test the Integration

1. **Start Django**: `python manage.py runserver`
2. **Go to Campaigns page**: `http://localhost:8000/campaigns/`
3. **Check status**: Look for "n8n Integration Status" in the sidebar
4. **Click "Test n8n Integration"** button
5. **Create a test campaign** and send it

## 🧪 Testing Steps

### Test 1: Status Check
- Go to `/campaigns/` page
- Check if status shows "n8n Enabled" (green) or "Direct Gmail" (amber)

### Test 2: Integration Test
- Click "Test n8n Integration" button
- Should show success message if n8n is reachable

### Test 3: Campaign Send
1. Create a campaign with at least one step
2. Add some test leads
3. Click "Send Now" on the campaign
4. Check Django logs for "Queuing via n8n" messages
5. Check n8n execution logs

### Test 4: Check MessageLog
- Go to Django admin or check database
- Look for `MessageLog` entries with `status='sent'`

## 🔧 Troubleshooting

### Status shows "Direct Gmail"
- Check that `USE_N8N_ORCHESTRATION=true`
- Verify `N8N_QUEUE_WEBHOOK_URL` is set
- Verify `N8N_HMAC_SECRET` is set

### Test fails with "n8n webhook returned 404"
- Make sure Workflow A is active in n8n
- Check the webhook URL is correct
- Verify n8n is running and accessible

### Test fails with "Invalid signature"
- Check that `N8N_HMAC_SECRET` matches in both Django and n8n
- Verify the secret doesn't have extra spaces or quotes

### Campaigns send but no emails arrive
- Check n8n execution logs for errors
- Verify Django `/webhook/n8n/send-now/` endpoint is working
- Check Gmail OAuth credentials are valid

## 📊 Monitoring

### Django Logs
```bash
tail -f logs/app.log | grep -i n8n
```

### n8n Execution Logs
- Go to n8n executions page
- Look for workflow executions
- Check for any error messages

### MessageLog Status
```python
# In Django shell
from myApp.models import MessageLog
MessageLog.objects.filter(status='sent').count()
MessageLog.objects.filter(status='failed').count()
```

## 🎯 What Happens When You Send a Campaign

1. **Django** creates campaign and steps
2. **User clicks "Send Now"** → Django `send_campaign` view
3. **Django checks** `USE_N8N_ORCHESTRATION` flag
4. **If enabled**: Django queues each lead via n8n webhook
5. **n8n receives** webhook, validates HMAC signature
6. **n8n waits** until `send_at` time (immediate for first step)
7. **n8n calls** Django `/webhook/n8n/send-now/`
8. **Django renders** email and sends via Gmail OAuth
9. **Django updates** MessageLog with `status='sent'`
10. **n8n marks** execution as successful

## 🔄 Fallback Mode

If n8n is not configured or fails:
- Django falls back to direct Gmail sending
- No delays or retries (immediate send)
- Still creates MessageLog entries
- Status shows "Direct Gmail" in UI

## 📝 Next Steps

Once basic integration works:
1. Set up proper n8n production instance
2. Configure monitoring and alerting
3. Add more complex campaign sequences
4. Implement property-triggered campaigns
5. Add campaign analytics and reporting
