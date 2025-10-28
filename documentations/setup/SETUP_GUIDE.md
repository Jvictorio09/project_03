# KaTek Real Estate Platform - Setup Guide

## Quick Start

1. **Clone and Install Dependencies**
   ```bash
   git clone <repository>
   cd project_03
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp ENV_SAMPLE.txt .env
   # Edit .env with your actual values
   ```

3. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py backfill_company_data
   python manage.py enforce_company_constraints
   ```

4. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## Required Environment Variables

### Core Settings
- `SECRET_KEY`: Django secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DEBUG`: Set to `False` in production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `ENVIRONMENT`: `development`, `staging`, or `production`

### Database
- `DATABASE_URL`: Database connection string
  - SQLite: `sqlite:///db.sqlite3`
  - PostgreSQL: `postgresql://user:password@host:port/database`

### Webhook Security
- `WEBHOOK_SIGNING_SECRET`: Secret key for webhook signature verification

### Email (Resend)
- `RESEND_API_KEY`: Your Resend API key
- `RESEND_FROM`: Sender email address (must be verified in Resend)
- `RESEND_REPLY_TO`: Reply-to email address

### Cloudinary
- `CLOUDINARY_CLOUD_NAME`: Your Cloudinary cloud name
- `CLOUDINARY_API_KEY`: Your Cloudinary API key
- `CLOUDINARY_API_SECRET`: Your Cloudinary API secret

### OpenAI
- `OPENAI_API_KEY`: Your OpenAI API key

## Feature Flags

The platform uses feature flags for gradual rollouts. Current flags in `myApp/services.py`:

- `property_creation`: ✅ Enabled - Property creation functionality
- `lead_autoresponder`: ✅ Enabled - Automatic email responses to leads
- `webhook_integration`: ✅ Enabled - n8n webhook integration
- `chat_widget`: ✅ Enabled - AI chat widget
- `ai_validation`: ✅ Enabled - AI property validation
- `property_iq_enrichment`: ❌ Disabled - Property IQ analysis
- `bulk_actions`: ❌ Disabled - Bulk property operations
- `advanced_analytics`: ❌ Disabled - Advanced analytics
- `property_estimates`: ❌ Disabled - Property market estimates
- `lead_crud`: ❌ Disabled - Lead management interface
- `campaign_management`: ❌ Disabled - Email campaign management

## Multi-Tenancy

The platform supports multi-tenancy with company-scoped data:

1. **Company Setup**: Each user must complete the setup wizard to create/join a company
2. **Data Isolation**: All data is automatically scoped to the user's company
3. **Company Switching**: Internal admin users can switch between companies

## API Endpoints

### Health Checks
- `GET /health/` - Quick health check
- `GET /readiness/` - Detailed readiness check (DB + outbox)

### Webhooks (n8n Integration)
- `POST /webhook/n8n/property-enrichment/` - Property enrichment results
- `POST /webhook/n8n/lead-processing/` - Lead processing results

### Modal Endpoints (HTMX)
- `GET /modal/add-property/` - Add property modal content
- `POST /modal/add-property/` - Create new property
- `GET /modal/sync-estimates/<property_id>/` - Sync property estimates
- `GET /modal/bulk-actions/` - Bulk actions modal

## Management Commands

```bash
# Backfill existing data with default company
python manage.py backfill_company_data

# Enforce company constraints
python manage.py enforce_company_constraints

# Process webhook messages
python manage.py process_webhooks

# Process webhooks with limit
python manage.py process_webhooks --limit 100
```

## Production Deployment

1. **Environment Variables**: Set all required environment variables
2. **Database**: Use PostgreSQL in production
3. **Static Files**: Run `python manage.py collectstatic`
4. **Webhooks**: Configure n8n webhook URLs in company settings
5. **Monitoring**: Set up log aggregation and error tracking
6. **Cron Jobs**: Schedule webhook processing:
   ```bash
   # Add to crontab
   */5 * * * * cd /path/to/project && python manage.py process_webhooks
   ```

## Security Considerations

1. **Webhook Signing**: All webhooks are signed with HMAC-SHA256
2. **CSRF Protection**: All forms include CSRF tokens
3. **Authentication**: Internal routes require login
4. **Data Isolation**: Company-scoped data access
5. **PII Masking**: Sensitive data is masked in logs

## Troubleshooting

### Common Issues

1. **Migration Errors**: Run `python manage.py migrate --fake-initial`
2. **Company Context Missing**: Ensure middleware is properly configured
3. **Webhook Failures**: Check `OutboxMessage` model for failed messages
4. **Email Not Sending**: Verify Resend API key and domain verification

### Logs

- Application logs: `logs/app.log`
- Request logs: JSON format with correlation IDs
- Error tracking: Configure Sentry for production

## Support

For issues and questions:
1. Check the logs for error details
2. Verify environment variables are set correctly
3. Ensure all required services are running
4. Check webhook delivery status in the admin panel
