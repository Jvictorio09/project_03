# Acceptance Testing Checklist

## Pre-Testing Setup

1. **Environment Configuration**
   - [ ] All environment variables are set correctly
   - [ ] Database is migrated and backfilled
   - [ ] Default company is created
   - [ ] Superuser account exists

2. **Feature Flags**
   - [ ] Property creation is enabled
   - [ ] Lead autoresponder is enabled
   - [ ] Webhook integration is enabled
   - [ ] Chat widget is enabled
   - [ ] AI validation is enabled

## Authentication & Access Control

### Login Flow
- [ ] Anonymous user visiting `/dashboard` → redirects to `/login/`
- [ ] Anonymous user visiting `/properties` → redirects to `/login/`
- [ ] Anonymous user visiting `/leads` → redirects to `/login/`
- [ ] Anonymous user visiting `/settings` → redirects to `/login/`

### Wizard Gating
- [ ] New user without company setup → redirects to `/setup/?step=1`
- [ ] User completes Step 1 (company profile) → can access dashboard
- [ ] User with company setup → can access all internal routes

### Public Routes
- [ ] Anonymous user can access `/` (home)
- [ ] Anonymous user can access `/list` (property search)
- [ ] Anonymous user can access `/property/<slug>/` (property details)
- [ ] Anonymous user can submit leads via `/lead/submit`

## Dashboard Testing

### Real Data Tiles
- [ ] Properties count shows actual company properties
- [ ] Leads count shows actual company leads
- [ ] Recent activity shows last 5 events
- [ ] No mock data is displayed

### Quick Actions
- [ ] "Add Property" button opens modal (if enabled)
- [ ] "Send Campaign" button is disabled with tooltip (if disabled)
- [ ] "Configure AI" button navigates to chat agent page

### Navigation
- [ ] "View All Properties" links to properties page
- [ ] All internal navigation works correctly

## Properties Page Testing

### Company Scoping
- [ ] Only shows properties for current company
- [ ] Search and filters work within company scope
- [ ] Pagination preserves company context

### Add Property Modal
- [ ] Modal opens when "Add Property" is clicked
- [ ] Form validation works correctly
- [ ] Successful submission creates property
- [ ] Property appears in list without page refresh
- [ ] Modal closes after successful submission

### Property Actions
- [ ] "Sync Estimates" button works (if enabled)
- [ ] Property details are editable
- [ ] Bulk actions work (if enabled)

## Lead Management Testing

### Lead Submission
- [ ] Public lead form works
- [ ] Duplicate detection works (same email/phone within 24h)
- [ ] Autoresponder email is sent (if email provided)
- [ ] Webhook message is created in outbox
- [ ] Lead appears in company leads list

### Lead Deduplication
- [ ] Same email within 24h returns friendly message
- [ ] Same phone within 24h returns friendly message
- [ ] Different email/phone creates new lead

## Feature Flag Testing

### Enabled Features
- [ ] Property creation works end-to-end
- [ ] Lead autoresponder sends emails
- [ ] Webhook integration creates outbox messages
- [ ] Chat widget is functional
- [ ] AI validation works

### Disabled Features
- [ ] Disabled buttons show tooltips
- [ ] Disabled features don't break the UI
- [ ] Tooltips explain "Coming soon" status

## Modal System Testing

### Accessibility
- [ ] Modal opens with focus on first input
- [ ] Tab navigation works within modal
- [ ] ESC key closes modal
- [ ] Clicking overlay closes modal
- [ ] Focus returns to trigger after closing

### HTMX Integration
- [ ] Modal content loads via HTMX
- [ ] Form submissions work without page reload
- [ ] Error handling keeps modal open
- [ ] Success responses close modal

## Webhook Integration Testing

### Outbox Processing
- [ ] Lead creation creates outbox message
- [ ] Property enrichment creates outbox message
- [ ] Webhook processing command works
- [ ] Failed webhooks retry with backoff
- [ ] Success updates message status

### n8n Callbacks
- [ ] Property enrichment callback updates property
- [ ] Lead processing callback updates lead
- [ ] Webhook signatures are verified
- [ ] Invalid signatures are rejected

## Search & Filtering Testing

### Company Scoping
- [ ] Search only returns company properties
- [ ] Filters work within company scope
- [ ] Pagination preserves filters and company context

### Performance
- [ ] Search results load quickly (<200ms)
- [ ] Filters don't cause timeouts
- [ ] Pagination works smoothly

## Email Testing

### Autoresponder
- [ ] Email is sent to lead's email address
- [ ] Email includes company branding
- [ ] Email includes related properties
- [ ] Email template renders correctly

### Email Configuration
- [ ] Resend API key is configured
- [ ] From address is verified
- [ ] Email sending doesn't break on errors

## Error Handling Testing

### Graceful Degradation
- [ ] Missing API keys don't break the app
- [ ] Network errors are handled gracefully
- [ ] Database errors show appropriate messages
- [ ] Webhook failures don't break lead creation

### User Experience
- [ ] Error messages are user-friendly
- [ ] Technical errors are logged appropriately
- [ ] Users can recover from errors

## Performance Testing

### Response Times
- [ ] Dashboard loads quickly
- [ ] Property list loads quickly
- [ ] Search results are fast
- [ ] Modal operations are responsive

### Database Queries
- [ ] No N+1 query problems
- [ ] Company scoping doesn't cause slow queries
- [ ] Pagination is efficient

## Security Testing

### Authentication
- [ ] Session management works correctly
- [ ] Logout clears session
- [ ] Password reset works

### Data Isolation
- [ ] Users can only see their company's data
- [ ] Company switching works correctly
- [ ] No data leakage between companies

### Webhook Security
- [ ] Webhook signatures are verified
- [ ] Invalid signatures are rejected
- [ ] Replay attacks are prevented

## Logging & Monitoring Testing

### Structured Logging
- [ ] Request logs include company context
- [ ] Error logs include correlation IDs
- [ ] PII is masked in logs
- [ ] Logs are in JSON format

### Health Endpoints
- [ ] `/health/` returns OK quickly
- [ ] `/readiness/` checks database and outbox
- [ ] Health checks work under load

## Final Checklist

### Core Functionality
- [ ] Multi-tenancy works correctly
- [ ] Authentication and authorization work
- [ ] Feature flags control functionality
- [ ] Modal system is accessible and functional
- [ ] Lead capture with deduplication works
- [ ] Property IQ enrichment works
- [ ] Search is fast and company-scoped
- [ ] Dashboard shows real data
- [ ] Observability features work
- [ ] Environment configuration is complete

### User Experience
- [ ] No dead buttons or broken links
- [ ] All forms work correctly
- [ ] Error messages are helpful
- [ ] Loading states are appropriate
- [ ] Mobile responsiveness is good

### Production Readiness
- [ ] All environment variables are documented
- [ ] Database migrations are ready
- [ ] Webhook processing is scheduled
- [ ] Logging is configured
- [ ] Health checks are working
- [ ] Security measures are in place

## Test Results

- [ ] All tests pass
- [ ] No critical issues found
- [ ] Performance is acceptable
- [ ] Security requirements met
- [ ] Ready for production deployment
