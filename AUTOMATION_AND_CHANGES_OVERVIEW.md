# Automation System and Updated Pages

## Overview
This document summarizes the automation capabilities added (email, Facebook, Instagram, webhooks) and lists all pages/files/routes/settings that were created or edited in this iteration.

## Automation Features
- Email automation
  - Welcome + follow-up sequences (Day 0/3/7/14)
  - Blast and sequence campaigns
  - Tracking via `MessageLog`
- Facebook Messenger integration
  - Page connection API + webhook receiver
  - AI responses with org persona and property context
  - Lead auto-capture + webhook outbox
- Instagram Direct integration (via Facebook Graph)
  - Account connection API + webhook receiver
  - AI responses + lead capture
- Webhook outbox processing
  - Reliable delivery with retries and HMAC signatures
- Background tasks (Celery-ready)
  - Process email sequences daily
  - Process webhook outbox / retries

## Updated/Added Files

### Models (updated)
- `myApp/models.py`
  - Added: `Organization`, `Membership`, `Plan`, `Subscription`, `PropertyEmbedding`, `Event`, `WebhookOutbox`, `Campaign`, `CampaignStep`, `MessageLog`
  - Updated: `Property` (adds `organization`, `is_active`), `Lead` (adds `organization`, `status`, `owner`, `attributes`, `conversation_id`, indexes)

### Middleware and Decorators (added)
- `myApp/middleware_organization.py`
  - `OrganizationContextMiddleware`, `OrganizationRequiredMiddleware`, `OrganizationPermissionsMiddleware`
- `myApp/decorators_organization.py`
  - `org_member_required`, `org_admin_required`, `org_owner_required`, `public_route`

### Services (added)
- `myApp/services_organization.py` (org lifecycle, plans, entitlements)
- `myApp/services_vector.py` (embeddings + property search)
- `myApp/services_lead.py` (lead capture + webhook delivery + qualification)
- `myApp/services_billing.py` (Stripe checkout + webhooks + entitlements)
- `myApp/services_email.py` (campaigns + sequences + delivery)
- `myApp/services_analytics.py` (dashboard metrics)
- `myApp/services_social.py` (Facebook/Instagram connect, webhooks, AI replies)

### Views and Routes (added/updated)
- `myApp/views_onboarding.py`
  - Onboarding steps 1–5, org creation, plan selection
  - Fixes slug creation and plan bootstrapping
- `myApp/views_chat.py`
  - Public ChatURL, API endpoint, embeddable widget JS
- `myApp/views_social.py`
  - Webhooks: `/webhook/facebook/`, `/webhook/instagram/`
  - Connect endpoints: `/api/connect/facebook/`, `/api/connect/instagram/`
- `myApp/urls.py` (updated)
  - Onboarding routes:
    - `GET /onboarding/` (wizard)
    - `POST /onboarding/step1/…/step5/`
  - Chat routes:
    - `GET /chat/<org_slug>`
    - `POST /api/chat/ask` (org-scoped)
    - `GET /embed/<org_slug>.js`
  - Social routes:
    - `POST /webhook/facebook/`, `POST /webhook/instagram/`
    - `POST /api/connect/facebook/`, `POST /api/connect/instagram/`

### Tasks and Commands (added)
- `myApp/tasks.py`
  - `process_email_sequences`, `process_webhook_outbox`, `send_lead_autoresponder`, `sync_facebook_messages`, `sync_instagram_messages`
- Management commands
  - `myApp/management/commands/init_platform.py` (plans + migrate legacy companies)
  - `myApp/management/commands/run_automations.py` (run email/webhook tasks)

### Templates (added)
- Onboarding
  - `myApp/templates/onboarding/step1_brand.html`
  - `myApp/templates/onboarding/step2_persona.html`
  - `myApp/templates/onboarding/step3_channels.html`
  - `myApp/templates/onboarding/step4_plan.html`
  - `myApp/templates/onboarding/step5_import.html`
- Chat (public/embed)
  - `myApp/templates/chat/public.html`
  - `myApp/templates/chat/embedded.html`
  - `myApp/templates/chat/unavailable.html`

### OAuth Adapters (added)
- `myApp/adapters.py` (create org on social signup, redirect flow)

### Settings (updated)
- `myProject/settings.py`
  - Middleware: adds `myApp.middleware_organization.*`
  - Database: supports `DATABASE_URL` (PostgreSQL) with fallback to SQLite
  - Stripe keys: `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
  - Email: `POSTMARK_API_TOKEN`, `POSTMARK_FROM_EMAIL`
  - Vector config: `VECTOR_DIMENSIONS`, `EMBEDDING_MODEL`
  - Social config: `FACEBOOK_VERIFY_TOKEN`, `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`
  - Celery: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, serializers

## New Endpoints (quick map)
- Onboarding
  - `GET /onboarding`, `POST /onboarding/step1..5`
- Chat
  - `GET /chat/<org_slug>`, `POST /api/chat/ask`, `GET /embed/<org_slug>.js`
- Social
  - `POST /webhook/facebook/`, `POST /webhook/instagram/`
  - `POST /api/connect/facebook/`, `POST /api/connect/instagram/`
- Automations
  - Management: `python manage.py run_automations --task [email|webhooks|all]`

## Environment Variables
```
OPENAI_API_KEY=...
STRIPE_PUBLISHABLE_KEY=...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
POSTMARK_API_TOKEN=...
POSTMARK_FROM_EMAIL=noreply@yourdomain.com
FACEBOOK_VERIFY_TOKEN=...
FACEBOOK_APP_ID=...
FACEBOOK_APP_SECRET=...
WEBHOOK_SIGNING_SECRET=...
N8N_WEBHOOK_URL=https://your-n8n/webhook/katek/ingest
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
DATABASE_URL=postgres://user:pass@host:port/db
```

## How to Run Automations
- Simple (cron): `python manage.py run_automations --task all`
- Celery (recommended):
  - `celery -A myProject beat -l info`
  - `celery -A myProject worker -l info`

## Notes
- All data is organization-scoped (multi-tenant). Always filter by `organization`.
- Social integrations require app verification on Facebook before production use.
