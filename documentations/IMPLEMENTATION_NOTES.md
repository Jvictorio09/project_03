# Implementation Notes

## Dashboard & n8n Migration

### Overview
This document summarizes the migration from Celery/Redis to n8n for background job processing, and the replacement of mock dashboard data with real, organization-scoped metrics.

### Changes Summary

#### 1. Data Model Additions
- **JobTask**: New model for storing background jobs (replaces Celery tasks)
- **JobEvent**: Optional event log for job lifecycle tracking
- **LeadMessage**: Unified message ingestion model for all channels (chat, email, Messenger, Instagram)
- **LeadPropertyLink**: Links messages to properties with confidence scores
- **ChannelConnection**: Tracks connection status for each channel per organization

#### 2. API Endpoints
- **GET /api/jobs/next**: Poll endpoint for n8n to fetch pending jobs
- **PATCH /api/jobs/<uuid>**: Update job status and results
- **POST /api/jobs/<uuid>/callback**: Webhook callback for job completion
- **POST /webhook/postmark/inbound**: Inbound email handler (Postmark)
- **GET /api/dashboard/timeseries**: Dashboard timeseries data API
- **GET /api/dashboard/recent-conversations**: Recent conversations API

#### 3. Dashboard Updates
- Removed all mock data from dashboard view
- Implemented real queries scoped to organization
- Added channel-aware filtering (only connected channels count)
- Implemented timeseries data with zero-fill for missing days
- Added recent conversations sidebar with real data

#### 4. Channel Integration
- Email: Postmark inbound webhook creates LeadMessage
- Chat: Existing chat flow creates LeadMessage
- Facebook Messenger: Webhook creates LeadMessage
- Instagram: Webhook creates LeadMessage
- All channels respect ChannelConnection.status

#### 5. Property Linking Pipeline
- Automatic property linking from messages
- Resolution order: explicit IDs → URL/slug → MLS → fuzzy match → vector search
- Confidence scores stored in LeadPropertyLink

#### 6. Background Jobs Migration
- Removed Celery dependency
- Jobs stored in database (JobTask model)
- n8n polls for jobs via REST API
- Retry logic and backoff handled in n8n workflows

#### 7. Feature Flags
- `FEATURE_DASHBOARD_REAL_DATA`: Controls new dashboard implementation
- Allows safe rollback if issues detected

### Migration Notes
- No breaking changes to existing OAuth flow
- No breaking changes to Stripe billing
- Existing model names preserved (Lead, Property)
- Existing webhook URLs preserved (extended, not replaced)

### Performance Considerations
- Added database indexes for dashboard queries
- Channel-aware filtering reduces query scope
- Timeseries queries optimized with date-based filtering

### Testing Checklist
See QA Plan section in API_CONTRACTS_DASHBOARD.md

