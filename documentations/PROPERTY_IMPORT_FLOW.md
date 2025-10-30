# Property Import Flow Documentation

## Overview

This document describes the end-to-end property import functionality implemented via HTMX endpoints. All endpoints return HTML fragments for modal body swapping - no full page reloads.

## Endpoints

### GET `/modal/add-property/`
**Purpose**: Returns the tabbed import UI fragment  
**Returns**: `properties/_import_modal.html` (fragment)

**Features**:
- Three tabs: Manual Form, AI Text Import, CSV Upload (disabled)
- Tab switching via JavaScript
- Content injected into modal body via HTMX

---

### POST `/import/manual/`
**Purpose**: Handle manual form submission  
**Form Fields**:
- `title` (required)
- `description` (required)
- `price_amount` (required)
- `city` (required)
- `area` (optional)
- `beds` (optional)
- `baths` (optional)
- `hero_image` (required, file upload)

**Process**:
1. Rate limit check (max 5 per minute per org/IP)
2. Validate form
3. Create `PropertyUpload` with status `uploading`
4. Upload image to Cloudinary (if provided)
5. Validate image size (max 10MB) and type (JPEG, PNG, WebP)
6. Transition to `processing` status
7. Start light AI validation
8. Return status fragment

**Returns**: `properties/_import_status.html` (fragment)

**Error Handling**:
- Form validation errors: Returns form with inline errors (400)
- Image too large: Error fragment (400)
- Invalid image type: Error fragment (400)
- Cloudinary failure: Error fragment (500)
- Rate limit exceeded: Error fragment (429)

---

### POST `/import/ai/`
**Purpose**: Handle AI text import  
**Form Fields**:
- `property_text` (required, textarea)
- `image_url` (optional, URL)

**Process**:
1. Rate limit check
2. Extract data using lightweight extraction:
   - Price (regex patterns)
   - Beds/Baths (regex)
   - City (keyword matching)
   - Area/Neighborhood (keyword matching)
   - Title (first line or sentence)
3. Create `PropertyUpload` with extracted data
4. Transition to `processing` status
5. Start light AI validation
6. Return status fragment with extracted preview

**Returns**: `properties/_import_status.html` (fragment with `extracted_preview`)

---

### POST `/import/csv/`
**Purpose**: Placeholder for CSV import  
**Returns**: Error fragment with "Coming soon" message (501)

---

### GET `/import/status/<upload_id>/`
**Purpose**: Pollable status endpoint  
**Returns**: `properties/_import_status.html` (fragment)

**Features**:
- Shows current `PropertyUpload.status`
- Displays extracted data preview (if available)
- Auto-polling every 2s if status is `processing`
- Stops polling when status changes
- Shows appropriate UI based on status:
  - `processing`: Spinner + "Validating Your Property..."
  - `validation`: "Continue Validation" button
  - `complete`: Success fragment or "Create Property" button

**HTMX Polling**:
```html
<div 
  hx-get="/import/status/{upload_id}/"
  hx-trigger="every 2s"
  hx-swap="outerHTML"
  hx-target="this">
</div>
```

---

### GET `/import/validate/<upload_id>/`
**Purpose**: Return validation chat fragment  
**Returns**: `properties/_import_validation.html` (fragment)

**Features**:
- Shows next required field question
- Displays chat history (last 5 messages)
- Single input field for user answer
- Example format shown if available

**Requirements**:
- `PropertyUpload.status` must be `validation`

---

### POST `/import/validate/<upload_id>/submit/`
**Purpose**: Handle validation chat reply  
**Form Fields**:
- `user_message` (required)

**Process**:
1. Append user message to `validation_chat_history`
2. Extract field value from answer and update `PropertyUpload`
3. Get AI response
4. Append AI response to chat history
5. Check if validation complete
6. If complete: Create Property, return success fragment
7. If incomplete: Return updated chat fragment with next question

**Returns**: 
- Success fragment if complete: `properties/_import_success.html`
- Updated chat fragment if incomplete: `properties/_import_validation.html`

---

### POST `/import/complete/<upload_id>/`
**Purpose**: Manually trigger completion (skip remaining validation)  
**Process**:
1. Create Property from upload
2. Link PropertyUpload to Property
3. Set status to `complete`
4. Send webhooks
5. Return success fragment

**Returns**: `properties/_import_success.html` (fragment)

---

### GET `/import/success/<property_id>/`
**Purpose**: Return success fragment (for direct access)  
**Returns**: `properties/_import_success.html` (fragment)

---

## Data Flow

```
User clicks "Add Property"
    ↓
GET /modal/add-property/
    ↓
Shows tabbed UI (Manual/AI/CSV)
    ↓
User submits form
    ↓
POST /import/manual/ or /import/ai/
    ↓
Creates PropertyUpload (status: uploading)
    ↓
Uploads image to Cloudinary (if provided)
    ↓
Status → processing
    ↓
Light AI validation runs
    ↓
Status → validation OR complete
    ↓
[If validation]
    GET /import/validate/<upload_id>/
    ↓
    User answers questions
    ↓
    POST /import/validate/<upload_id>/submit/
    ↓
    Updates PropertyUpload
    ↓
    [Loop until complete]
    ↓
[If complete]
    POST /import/complete/<upload_id>/
    ↓
    Creates Property object
    ↓
    Returns success fragment
```

---

## Rate Limiting

**Limit**: 5 uploads per minute per organization/IP  
**Implementation**: Django cache with 60-second TTL  
**Key Format**: `import_rate_limit:{org_id}:{ip}`

**Response**: HTTP 429 with error fragment

---

## Image Upload

**Max Size**: 10MB  
**Allowed Types**: JPEG, JPG, PNG, WebP  
**Storage**: Cloudinary  
**Validation**: Server-side (before upload)

**Error Responses**:
- Too large: "Image file is too large. Maximum size is 10MB."
- Invalid type: "Invalid image type. Please upload JPEG, PNG, or WebP images only."
- Upload failure: "Failed to upload image. Please check your connection and try again."

---

## AI Validation

### Light Pass (Inline)
Runs synchronously when upload transitions to `processing`:

1. Checks critical fields:
   - Title
   - Price
   - City

2. Initializes `ai_validation_result`:
   ```json
   {
     "property_identification": "complete|partial|missing",
     "location_details": "complete|partial|missing",
     "financial_info": "complete|partial|missing"
   }
   ```

3. Populates `missing_fields` list

4. Sets status:
   - If no critical fields missing → `complete`
   - Else → `validation`

### Deep Pass (Async)
Emitted as `JobTask` for n8n processing:
- `kind`: `property_validation_deep`
- `payload`: `{"upload_id": "<uuid>"}`

When n8n callback returns, `ai_validation_result` and `missing_fields` are updated.

---

## Validation Chat

### Next Question Logic
Questions are prioritized based on `missing_fields` list:
1. Property Title
2. Price
3. City
4. Full Street Address

### Field Extraction
Simple pattern matching extracts values from user answers:
- Price: `\$?([0-9,]+)`
- Address: Stored in description with prefix "Address: "
- City: First 64 characters

### Completion Check
Critical fields must be present:
- Property Title ✅
- Price ✅
- City ✅

---

## Property Creation

### Slug Generation
1. Slugify title
2. Check uniqueness within organization
3. Append counter if duplicate (e.g., `property-2`)

### Description Consolidation
1. Initial description from form/AI extraction
2. Append chat history summary (last 5 user messages)
3. Format: "Additional Information:\n- {message}\n"

### Webhooks Sent
1. **Property Listing Webhook** (`send_property_listing_webhook`)
   - Property data
   - Upload metadata
   - Validation results

2. **Property Enrichment Webhook** (optional, if configured)
   - For AVM/location enrichment

---

## Error Handling

### HTMX Error Listeners (Frontend)

**Global Listeners**:
- `htmx:responseError`: Shows toast + injects error fragment
- `htmx:sendError`: Shows network error toast
- `htmx:afterRequest`: Handles 422 validation errors

**Error Fragment**: `properties/_error_fragment.html`
- Shows error message
- Optional error details (collapsible)
- Close button

### Server-Side Error Handling

**Try/Catch Blocks**:
- All endpoints wrapped in try/catch
- Errors logged with context (org_id, user_id, upload_id)
- Meaningful error messages returned in fragments

**HTTP Status Codes**:
- 400: Bad Request (validation errors, missing fields)
- 429: Too Many Requests (rate limit)
- 500: Internal Server Error (unexpected errors)
- 501: Not Implemented (CSV import)

---

## Permissions & Security

### Authentication
- All endpoints require `@login_required`
- Organization resolved from `request.organization` (set by middleware)
- Fallback: User's active membership

### CSRF Protection
- All POST endpoints require CSRF token
- HTMX automatically includes token from cookies
- Forms include `{% csrf_token %}`

### Organization Scoping
- All queries filtered by `organization`
- PropertyUpload scoped to organization
- Property creation scoped to organization

---

## Environment Variables

Required in `.env`:

```bash
# Cloudinary (for image uploads)
CLOUDINARY_STORAGE_CLOUD_NAME=your_cloud_name
CLOUDINARY_STORAGE_API_KEY=your_api_key
CLOUDINARY_STORAGE_API_SECRET=your_api_secret

# OpenAI (for AI validation - optional)
OPENAI_API_KEY=your_openai_key

# Cache (for rate limiting)
CACHES=...
```

---

## Testing Checklist

### Manual Success Path
- [ ] Fill form with all fields → status → complete → property appears in list

### Manual Missing Data
- [ ] Omit Address → see validation chat → provide address → complete

### AI Text Path
- [ ] Paste MLS-like text → fields extracted → either complete or prompt for 1-2 items

### Cloudinary Failure
- [ ] Simulate upload error → error fragment appears, no PropertyUpload created

### Duplicate Title
- [ ] Import same title twice → slugs end up unique (e.g., -2)

### Rate Limit
- [ ] Submit 6 imports in under a minute → graceful rate-limit error fragment

### Error Handling
- [ ] Simulate network error → toast notification appears
- [ ] Invalid form data → inline errors shown
- [ ] Server error → error fragment in modal

---

## Troubleshooting

### Button doesn't open modal
- Check: `add_property_modal` URL exists
- Check: HTMX library loaded
- Check: Modal shell exists on page

### Modal content doesn't load
- Check: Server returns fragment (not full page)
- Check: No 302 redirects
- Check: HTMX `hx-target` selector matches `.modal-body`

### Form submission fails silently
- Check: CSRF token present
- Check: HTMX error listeners attached
- Check: Server logs for errors

### Status polling doesn't stop
- Check: Status changes from `processing`
- Check: HTMX trigger condition

### Property not created
- Check: Validation complete (all critical fields present)
- Check: Organization exists
- Check: Server logs for errors

---

## Related Files

- `myApp/views_properties_import.py`: All endpoint implementations
- `myApp/templates/properties/_import_*.html`: Fragment templates
- `myApp/templates/properties.html`: Main page with modal shell
- `myApp/models.py`: PropertyUpload and Property models
- `myApp/utils/cloudinary_utils.py`: Image upload utilities

