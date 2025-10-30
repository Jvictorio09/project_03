# Property Import Functionality Guide

## Overview

The Property Import feature allows real estate agents and organizations to add properties to their inventory through multiple methods. The system uses AI-powered validation to ensure property data is complete and accurate before making properties live.

## Purpose

The import properties feature serves to:
- **Streamline property onboarding**: Quickly add properties from various sources
- **Ensure data quality**: AI validation ensures all critical fields are filled
- **Interactive data collection**: Chat-based interface guides users through missing information
- **Batch processing**: Support for multiple property uploads
- **Organization-scoped**: All properties are tied to an organization for multi-tenancy

---

## Data Models

### PropertyUpload Model

Temporary staging table that holds property data during the import/validation process.

```python
class PropertyUpload(models.Model):
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),      # Initial upload stage
        ('processing', 'Processing'),   # AI validation in progress
        ('validation', 'Validation'),    # User interaction needed
        ('complete', 'Complete'),        # Property created successfully
        ('failed', 'Failed'),           # Import failed
    ]
    
    # Basic property fields
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    price_amount = models.IntegerField(null=True, blank=True)
    city = models.CharField(max_length=64, blank=True)
    area = models.CharField(max_length=64, blank=True)
    beds = models.IntegerField(null=True, blank=True)
    baths = models.IntegerField(null=True, blank=True)
    hero_image = models.URLField(blank=True)  # Cloudinary URL
    
    # AI validation data
    ai_validation_result = models.JSONField(default=dict)
    missing_fields = models.JSONField(default=list)
    validation_chat_history = models.JSONField(default=list)
    consolidated_information = models.TextField(blank=True)
    
    # Relationship
    property = models.OneToOneField(Property, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Property Model

The final property object that gets created after successful validation.

```python
class Property(models.Model):
    id = models.UUIDField(primary_key=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price_amount = models.IntegerField()
    city = models.CharField(max_length=64)
    area = models.CharField(max_length=64, blank=True)
    beds = models.IntegerField(default=1)
    baths = models.IntegerField(default=1)
    floor_area_sqm = models.IntegerField(default=0)
    parking = models.BooleanField(default=False)
    hero_image = models.URLField(blank=True)
    badges = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## Import Methods

### 1. Manual Form Upload (`upload_listing`)

**Route**: `/upload-listing/`  
**View**: `upload_listing`  
**Form**: `PropertyUploadForm`

**Fields**:
- Title
- Description
- Price Amount (USD)
- City (dropdown)
- Area/Neighborhood
- Beds
- Baths
- Hero Image (file upload)

**Process**:
1. User fills out form and submits
2. Creates `PropertyUpload` with status `uploading`
3. Image is uploaded to Cloudinary
4. Status changes to `processing`
5. AI validation begins automatically
6. Redirects to processing page

**Code Example**:
```python
def upload_listing(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = PropertyUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save()
            upload.status = 'processing'
            upload.save()
            validate_property_with_ai(upload)
            return redirect('processing_listing', upload_id=upload.id)
    else:
        form = PropertyUploadForm()
    return render(request, 'upload_listing.html', {'form': form})
```

---

### 2. AI-Powered Text Import (`process_ai_prompt`)

**Route**: `/process-ai-prompt/`  
**View**: `process_ai_prompt`  
**Method**: POST

**Input**: Natural language property description

**Process**:
1. User pastes property description (e.g., from MLS, email, etc.)
2. AI extracts structured data:
   - Title
   - Price
   - Beds/Baths
   - City/Area
   - Other features
3. Creates `PropertyUpload` with extracted data
4. Starts AI validation
5. Returns preview data

**Example Input**:
```
"Luxury 2BR condo in BGC, Makati. 
$3,500/month. 
2 bedrooms, 2 baths. 
Modern amenities, pool, gym.
Contact Maria at 0917-123-4567"
```

**AI Extraction**:
- Title: "Luxury 2BR Condo in BGC"
- Price: 3500
- Beds: 2
- Baths: 2
- City: "Makati"
- Area: "BGC"

---

### 3. Property Enrichment Webhook (`property_enrichment`)

**Route**: `/webhook/property-enrichment/`  
**View**: `property_enrichment_webhook`  
**Method**: POST

**Purpose**: External systems (n8n, CRM, MLS) can push property data

**Payload**:
```json
{
  "property_id": "uuid",
  "organization_id": "uuid",
  "title": "Property Title",
  "description": "Full description...",
  "price_amount": 3500,
  "city": "Makati",
  "area": "BGC",
  "beds": 2,
  "baths": 2,
  "floor_area_sqm": 85,
  "parking": true,
  "hero_image": "https://cloudinary.com/image.jpg",
  "additional_data": {}
}
```

**Process**:
1. Webhook receives property data
2. Validates organization exists
3. Creates/updates PropertyUpload
4. Initiates AI validation
5. Returns status

---

## Import Flow Diagram

```
┌─────────────────┐
│  User Starts    │
│  Import Process │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Create         │
│  PropertyUpload │
│  (status:       │
│   uploading)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Upload Image   │
│  to Cloudinary  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Status:        │
│  processing     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI Validation  │
│  (OpenAI GPT)   │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────┐
│  All Fields     │  │ Missing      │
│  Complete?     │  │ Fields       │
│                 │  │              │
│  YES           │  │ NO           │
└────────┬────────┘  └──────┬───────┘
         │                   │
         │                   ▼
         │          ┌─────────────────┐
         │          │ Status:         │
         │          │ validation      │
         │          └────────┬────────┘
         │                   │
         │                   ▼
         │          ┌─────────────────┐
         │          │ Validation Chat │
         │          │ (AI asks for    │
         │          │  missing info)  │
         │          └────────┬────────┘
         │                   │
         │                   │ User provides info
         │                   │
         │                   ▼
         │          ┌─────────────────┐
         │          │ Check Complete? │
         │          └────────┬────────┘
         │                   │
         └───────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ Status:         │
         │ complete        │
         └────────┬────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ Create Property │
         │ Object          │
         └────────┬────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ Link Property   │
         │ to Upload       │
         └────────┬────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ Send Webhooks   │
         │ (n8n, CRM)      │
         └─────────────────┘
```

---

## AI Validation Process

### Step 1: Initial Validation (`validate_property_with_ai`)

**Purpose**: Analyze uploaded property data against comprehensive checklist

**Checklist Sections**:
1. **Property Identification**
   - MLS Number
   - Property Type
   - Listing Status
   - Agent Info

2. **Location Details**
   - Full Street Address
   - County/Subdivision
   - School District
   - Landmarks

3. **Lot & Building**
   - Lot Size
   - Year Built
   - Living Area
   - Stories/Basement
   - Parking

4. **Interior Features**
   - Kitchen Details
   - Flooring
   - HVAC
   - Fireplace
   - Energy Efficiency

5. **Property Features**
   - Outdoor Spaces
   - HOA Amenities
   - Security
   - Views

6. **Financial Info**
   - List Price
   - Price per sq ft
   - HOA Fees
   - Property Taxes

7. **Legal Info**
   - Title Status
   - Parcel Number
   - Zoning
   - Flood Zone

8. **Media Assets**
   - Professional Photos
   - Floor Plans
   - Virtual Tours

9. **Documentation**
   - Disclosures
   - Inspection Reports
   - Permits

**AI Response Format**:
```json
{
  "property_identification": "complete",
  "location_details": "partial",
  "lot_building": "missing",
  "interior_features": "complete",
  "property_features": "partial",
  "financial_info": "complete",
  "legal_info": "missing",
  "media_assets": "complete",
  "documentation": "missing"
}
```

**Missing Fields Extraction**:
```json
{
  "missing_fields": [
    "Full Street Address",
    "Lot Size",
    "Year Built",
    "Title Status",
    "Parcel Number"
  ]
}
```

---

### Step 2: Validation Chat (`validation_chat`)

**Purpose**: Interactive conversation to collect missing information

**Flow**:
1. User redirected to `/validation-chat/<upload_id>/`
2. AI asks ONE question at a time about missing fields
3. User responds with information
4. AI acknowledges and moves to next missing field
5. Process continues until all critical fields are complete

**Example Conversation**:

```
AI: "I see you have a property listing in Makati. To complete this listing, 
     I need the full street address. Please provide it in this format:
     123 Main Street, Barangay, City, ZIP Code."

User: "15th Floor, One Parkade, 16th Avenue, Fort Bonifacio, Taguig City, 1634"

AI: "Perfect! Thank you. Now I need to know about the lot size. 
     Please provide it in square feet or square meters. 
     For example: '500 sqm' or '5,382 sq ft'."
```

**Chat History Storage**:
```json
[
  {
    "role": "assistant",
    "content": "I need the full street address...",
    "timestamp": "2025-10-29T10:00:00Z"
  },
  {
    "role": "user",
    "content": "15th Floor, One Parkade...",
    "timestamp": "2025-10-29T10:01:00Z"
  }
]
```

**Completion Check** (`check_validation_complete`):
- All critical fields must be marked as `complete` or `partial`
- No `missing` status for essential sections
- Minimum required fields:
  - Title ✅
  - Address ✅
  - Price ✅
  - City ✅
  - Property Type ✅

---

### Step 3: Property Creation (`create_property_from_upload`)

**Purpose**: Convert validated PropertyUpload into live Property object

**Process**:
1. Generate unique slug from title
2. Consolidate all information from chat history
3. Create Property object with complete data
4. Link PropertyUpload to Property
5. Send webhooks to external systems
6. Trigger property enrichment workflow

**Code**:
```python
def create_property_from_upload(upload: PropertyUpload):
    # Generate unique slug
    base_slug = slugify(upload.title)
    slug = base_slug
    counter = 1
    while Property.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Consolidate information
    consolidated_info = consolidate_property_information(upload)
    
    # Create Property
    property_obj = Property.objects.create(
        title=upload.title,
        description=consolidated_info,
        price_amount=upload.price_amount,
        city=upload.city,
        area=upload.area,
        beds=upload.beds or 1,
        baths=upload.baths or 1,
        slug=slug,
        hero_image=upload.hero_image,
        badges="AI-Validated, Complete Listing",
        organization=upload.organization  # Set organization
    )
    
    # Link PropertyUpload to Property
    upload.property = property_obj
    upload.status = 'complete'
    upload.save()
    
    # Send webhooks
    send_property_listing_webhook(property_data)
    send_property_enrichment_webhook(enrichment_data)
```

---

## Status Transitions

```
uploading → processing → validation → complete
                              │
                              ├─→ failed (if validation fails)
                              │
                              └─→ processing (if user provides info)
```

**Status Descriptions**:

| Status | Description | Next Action |
|--------|-------------|-------------|
| `uploading` | Initial upload stage | Auto-transition to `processing` |
| `processing` | AI validation in progress | Auto-transition to `validation` or `complete` |
| `validation` | User interaction needed | User answers questions in chat |
| `complete` | Property created successfully | Property is live |
| `failed` | Import failed | User can retry or delete |

---

## API Endpoints

### POST `/upload-listing/`
**Body**: Form data (multipart/form-data)
- `title`: string
- `description`: text
- `price_amount`: integer
- `city`: string
- `area`: string
- `beds`: integer
- `baths`: integer
- `hero_image`: file

**Response**: Redirect to `/processing-listing/<upload_id>/`

---

### POST `/process-ai-prompt/`
**Body**: JSON
```json
{
  "property_description": "Luxury 2BR condo...",
  "additional_info": "Contact info, etc."
}
```

**Response**: JSON
```json
{
  "success": true,
  "upload_id": "uuid",
  "preview": {
    "title": "Luxury 2BR Condo",
    "price": 3500,
    "beds": 2,
    "baths": 2,
    "city": "Makati"
  }
}
```

---

### POST `/validation-chat/<upload_id>/`
**Body**: Form data
- `user_message`: string

**Response**: Redirect to same page with updated chat history

---

### POST `/webhook/property-enrichment/`
**Body**: JSON (see webhook payload above)

**Response**: JSON
```json
{
  "success": true,
  "upload_id": "uuid",
  "status": "processing"
}
```

---

## Integration Points

### 1. Cloudinary (Image Storage)
- All hero images uploaded to Cloudinary
- URL stored in `PropertyUpload.hero_image`
- Automatic optimization and CDN delivery

### 2. OpenAI (AI Validation)
- GPT-4 for property data extraction
- GPT-4 for validation chat responses
- Structured data validation

### 3. Webhooks (External Systems)
- **Property Listing Webhook**: Sent when property is created
- **Property Enrichment Webhook**: Sent for enrichment workflows
- **Validation Chat Webhook**: Sent during chat interactions

### 4. n8n Workflows
- Property enrichment automation
- Data synchronization with CRM
- Lead generation triggers

---

## Usage Examples

### Example 1: Manual Form Upload

```python
# 1. User navigates to /upload-listing/
# 2. Fills form:
#    - Title: "Modern 2BR Condo in BGC"
#    - Description: "Spacious unit with city views..."
#    - Price: 3500
#    - City: Makati
#    - Area: BGC
#    - Beds: 2
#    - Baths: 2
#    - Image: uploads photo

# 3. Submit → Creates PropertyUpload
# 4. Redirects to /processing-listing/<upload_id>/
# 5. AI validation runs automatically
# 6. If missing fields → redirects to /validation-chat/<upload_id>/
# 7. User answers questions
# 8. Property created when complete
```

### Example 2: AI Text Import

```python
# 1. User pastes text:
#    "Luxury penthouse in Rockwell. 3BR, 3BA. 
#     $8,500/month. Includes pool, gym, concierge."

# 2. POST to /process-ai-prompt/
# 3. AI extracts:
#    - Title: "Luxury Penthouse"
#    - Price: 8500
#    - Beds: 3
#    - Baths: 3
#    - City: "Makati" (from context)
#    - Area: "Rockwell"

# 4. Creates PropertyUpload with extracted data
# 5. Validation process continues...
```

### Example 3: Webhook Import

```python
# External system (MLS, CRM) sends:
POST /webhook/property-enrichment/
{
  "organization_id": "uuid",
  "title": "Spacious 4BR House",
  "price_amount": 12000,
  "city": "Quezon City",
  "beds": 4,
  "baths": 3,
  "hero_image": "https://..."
}

# System creates PropertyUpload
# Validation begins automatically
# Property created when complete
```

---

## Error Handling

### Common Errors

1. **Missing Organization**
   - Error: "Organization not found"
   - Fix: Ensure user has active organization membership

2. **Image Upload Failure**
   - Error: "Failed to upload image to Cloudinary"
   - Fix: Check Cloudinary credentials, file size limits

3. **AI Validation Timeout**
   - Error: "OpenAI API timeout"
   - Fix: Retry validation, check API key

4. **Duplicate Slug**
   - Error: "Slug already exists"
   - Fix: Auto-appends counter (e.g., "property-2")

5. **Validation Chat Failure**
   - Error: "Failed to process chat message"
   - Fix: Check OpenAI API, retry message

---

## Best Practices

1. **Always provide complete initial data**: Reduces validation chat time
2. **Use clear property descriptions**: Helps AI extraction accuracy
3. **Upload high-quality images**: Better user experience
4. **Complete validation chat**: Ensures data quality
5. **Monitor webhook responses**: Track external system integration

---

## Future Enhancements

- [ ] Bulk import via CSV/Excel
- [ ] MLS API integration
- [ ] Automated property enrichment from external sources
- [ ] Image recognition for property features
- [ ] Duplicate detection
- [ ] Property comparison tools
- [ ] Advanced validation rules per organization

---

## Related Documentation

- [Property Enrichment Storyboard](./PROPERTY_ENRICHMENT_STORYBOARD.md)
- [n8n Automation Requirements](./N8N_AUTOMATION_REQUIREMENTS.md)
- [API Contracts](./API_CONTRACTS_DASHBOARD.md)

