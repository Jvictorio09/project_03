# System Architecture Documentation

## 🏗️ System Overview

This is a **Real Estate Property Listing Platform** built with Django that combines traditional property search with AI-powered property validation and chat functionality. The system integrates with Katalyst CRM via webhooks for lead tracking and analytics.

---

## 📊 Data Models (myApp/models.py)

### 1. **Property Model**
The core property listing model:
- **Fields:**
  - `id`: UUID primary key
  - `slug`: Unique URL-friendly identifier
  - `title`: Property title
  - `description`: Full property description
  - `price_amount`: Monthly rent/price (integer)
  - `city`: Property city
  - `area`: Neighborhood/area
  - `beds`: Number of bedrooms
  - `baths`: Number of bathrooms
  - `floor_area_sqm`: Floor area in square meters
  - `parking`: Boolean for parking availability
  - `hero_image`: URL to main property image
  - `badges`: Comma-separated tags (e.g., "AI-Validated, Complete Listing")
  - `affiliate_source`: Source of listing
  - `commissionable`: Whether commission applies
  - `created_at`: Timestamp

### 2. **Lead Model**
Captures potential customer information:
- **Fields:**
  - `id`: UUID primary key
  - `name`: Lead name
  - `phone`: Contact phone
  - `email`: Email address
  - `buy_or_rent`: Choice field (rent/buy)
  - `budget_max`: Maximum budget
  - `beds`: Desired bedrooms
  - `areas`: Interested areas (comma-separated)
  - `interest_ids`: Property IDs of interest
  - `utm_source`, `utm_campaign`, `referrer`: Tracking fields
  - `consent_contact`: GDPR consent
  - `created_at`: Timestamp

### 3. **PropertyUpload Model**
Manages the property upload and AI validation process:
- **Fields:**
  - `id`: UUID primary key
  - `property`: OneToOne link to final Property (nullable)
  - `status`: Current status (uploading, processing, validation, complete, failed)
  - `title`, `description`, `price_amount`, `city`, `area`, `beds`, `baths`: Initial data
  - `hero_image`: ImageField for uploaded photo
  - `ai_validation_result`: JSON field storing AI analysis
  - `missing_fields`: JSON array of missing information
  - `validation_chat_history`: JSON array of chat messages
  - `consolidated_information`: Final consolidated description
  - `created_at`, `updated_at`: Timestamps

---

## 🔗 URL Routes (myApp/urls.py)

| Route | View Function | Purpose |
|-------|--------------|---------|
| `/` | `home()` | Homepage with featured properties |
| `/list` | `results()` | Property search results (traditional & AI) |
| `/property/<slug>/` | `property_detail()` | Individual property page |
| `/property/<slug>/chat` | `property_chat()` | HTMX chat endpoint |
| `/lead/submit` | `lead_submit()` | Lead form submission |
| `/book` | `book()` | Booking page |
| `/thanks` | `thanks()` | Thank you page after lead submission |
| `/dashboard` | `dashboard()` | Internal listings dashboard |
| `/health/` | `health_check()` | Railway health check |
| `/upload-listing/` | `upload_listing()` | Simple property upload |
| `/processing/<uuid>/` | `processing_listing()` | Processing status page |
| `/validation/<uuid>/` | `validation_chat()` | AI validation chat interface |
| `/listing-choice/` | `listing_choice()` | Choose upload method |
| `/ai-prompt-listing/` | `ai_prompt_listing()` | AI prompt-based upload |
| `/manual-form-listing/` | `manual_form_listing()` | Comprehensive manual form |

---

## 🎯 Core Features & Functions

### **1. Property Search System**

#### Traditional Search (`results()` view)
- **Location:** `views.py:24-86`
- **Functionality:**
  - Filters by query string, city, beds, price_max
  - Uses Django Q objects for complex queries
  - Searches across title, description, badges, city
  
#### AI Prompt Search (`process_ai_search_prompt()`)
- **Location:** `views.py:272-346`
- **Functionality:**
  - Processes natural language queries (e.g., "2 bedroom in LA under $3000")
  - Extracts: city, bedrooms, price, buy/rent intent, keywords
  - Uses regex patterns and keyword matching
  - Sends search data to CRM via webhook
  - Returns structured search parameters

**Data Flow:**
```
User enters prompt → process_ai_search_prompt() → Extract parameters →
Filter properties → Send webhook → Display results
```

---

### **2. Property Chat System**

#### Chat Endpoint (`property_chat()`)
- **Location:** `views.py:217-258`
- **Functionality:**
  - HTMX-powered real-time chat
  - Rule-based question answering
  - Sends chat data to CRM webhook
  - Returns chat bubble HTML partial

#### Simple Answer Engine (`simple_answer()`)
- **Location:** `views.py:349-397`
- **Responses to:**
  - Price/rent questions
  - Bedroom/bathroom counts
  - Size/area information
  - Parking availability
  - Location with Google Maps links
  - Availability inquiries
  - Fees/deposits
  - Fallback to agent contact

**Data Flow:**
```
User message → property_chat() → simple_answer() → 
Generate response → Send webhook → Return HTML bubble
```

---

### **3. Lead Capture System**

#### Lead Submission (`lead_submit()`)
- **Location:** `views.py:93-142`
- **Functionality:**
  - Handles POST requests with `LeadForm`
  - Captures UTM parameters and referrer
  - Stores interest_ids (property IDs)
  - Sends lead data to CRM webhook
  - HTMX-aware responses (partial or full redirect)

**Data Flow:**
```
Form submission → Validate → Capture tracking → Save lead →
Send webhook → Return success partial/redirect to thanks
```

---

### **4. AI Property Upload & Validation System**

This is the most complex feature with multiple pathways:

#### **Path 1: Simple Upload** (`upload_listing()`)
- **Location:** `views.py:399-415`
- Basic form submission
- Triggers AI validation
- Redirects to processing

#### **Path 2: AI Prompt Upload** (`ai_prompt_listing()`)
- **Location:** `views.py:1297-1324`
- User provides natural language description + photo
- Processes with `process_ai_prompt_with_validation()`
- Extracts structured data from unstructured text
- Goes to validation chat

#### **Path 3: Manual Form Upload** (`manual_form_listing()`)
- **Location:** `views.py:1327-1378`
- Comprehensive structured form
- Stores extensive property details in JSON
- Light validation with suggestions
- Can skip validation if complete

#### AI Validation Process

**Step 1: Initial Validation** (`validate_property_with_ai()`)
- **Location:** `views.py:513-753`
- **Process:**
  1. Sends property data to OpenAI GPT-4
  2. Uses comprehensive real estate checklist prompt
  3. Evaluates 9 sections of property information:
     - 🏡 Property Identification
     - 📍 Location Details
     - 📐 Lot & Building Information
     - 🛋 Interior Features
     - 🏢 Property Features & Amenities
     - 💰 Pricing & Financial Information
     - 📜 Legal & Ownership Information
     - 🖼 Media & Marketing Assets
     - 📎 Documentation & Disclosures
  4. Returns JSON with validation status and missing fields
  5. Sets status to 'validation'
  6. Initializes chat history

**Step 2: Validation Chat** (`validation_chat()`)
- **Location:** `views.py:431-510`
- **Process:**
  1. Displays chat interface with completion percentage
  2. User provides missing information
  3. Each response processed by `get_ai_validation_response()`
  4. Sends interaction to CRM webhook
  5. Checks completion with `check_validation_complete()`
  6. When complete, creates final Property object

**Step 3: AI Chat Response** (`get_ai_validation_response()`)
- **Location:** `views.py:756-845`
- **Process:**
  1. Builds context from chat history and property data
  2. Sends to GPT-4 for intelligent response
  3. AI asks for specific missing information
  4. Provides examples and format guidance
  5. Acknowledges provided info and moves to next field
  6. Falls back to `get_specific_fallback_response()` if API fails

**Step 4: Fallback Responses** (`get_specific_fallback_response()`)
- **Location:** `views.py:848-934`
- Detailed question templates for each missing field
- Keyword-based response matching
- Systematic progression through missing fields

**Step 5: Completion Check** (`check_validation_complete()`)
- **Location:** `views.py:937-953`
- Flexible validation (basic required: title, price, city)
- Allows completion after 3+ user messages
- User-friendly approach

**Step 6: Property Creation** (`create_property_from_upload()`)
- **Location:** `views.py:956-1020`
- Creates unique slug
- Consolidates all information
- Creates final Property object
- Links to PropertyUpload
- Sends listing webhook to CRM

**Step 7: Information Consolidation** (`consolidate_property_information()`)
- **Location:** `views.py:1023-1107`
- Uses GPT-4 to create professional description
- Combines upload data + chat responses
- Generates 200-300 word marketing copy
- Stores in consolidated_information field

**Data Flow:**
```
Upload form → Create PropertyUpload → validate_property_with_ai() →
AI analyzes → Missing fields identified → validation_chat() →
User provides info → get_ai_validation_response() → Check complete →
consolidate_property_information() → create_property_from_upload() →
Final Property created → Webhook sent → Redirect to property detail
```

---

### **5. Dashboard System**

#### Internal Dashboard (`dashboard()`)
- **Location:** `views.py:161-214`
- **Features:**
  - Search by query, city
  - Sort by: new, price (asc/desc), beds
  - Pagination (12-48 per page)
  - Filter dropdowns for cities
  - Total count display

---

## 📡 Webhook Integration (myApp/webhook.py)

### Webhook Endpoints

1. **CHAT_INQUIRY_WEBHOOK**
   - URL: `https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545ponse`
   - Used for: leads, chat inquiries, validation chat, prompt searches

2. **PROPERTY_LISTING_WEBHOOK**
   - URL: `https://katalyst-crm.fly.dev/webhook-test/7e36f0ef-e0b2-498d-886c-f06bef9afd80`
   - Used for: new property listings

### Webhook Functions

#### `send_chat_inquiry_webhook(lead_data)`
- **Location:** `webhook.py:51-85`
- **Triggers:**
  - Lead form submission
  - Validation chat interactions
  - Property chat messages (as "Property_inquiry")
  - AI prompt searches
- **Payload Structure:**
  ```json
  {
    "type": "chat_inquiry" or "Property_inquiry",
    "timestamp": "ISO format",
    "session_id": "session key",
    "lead": { /* lead details */ },
    "tracking": { /* UTM params */ },
    "property": { /* property context */ }
  }
  ```

#### `send_property_listing_webhook(property_data)`
- **Location:** `webhook.py:88-127`
- **Triggers:**
  - Property creation from validated upload
- **Payload Structure:**
  ```json
  {
    "type": "property_listing",
    "timestamp": "ISO format",
    "property": { /* full property data */ },
    "upload_info": {
      "validation_result": {},
      "missing_fields": [],
      "consolidated_information": ""
    },
    "source": "ai_validation"
  }
  ```

#### `send_property_chat_webhook(chat_data)`
- **Location:** `webhook.py:130-162`
- **Triggers:**
  - Property detail page chat
- **Type:** "Property_inquiry"

#### `send_prompt_search_webhook(search_data)`
- **Location:** `webhook.py:165-208`
- **Triggers:**
  - AI prompt-based property search
- **Type:** "Property_inquiry"

---

## 📋 Forms (myApp/forms.py)

### 1. **LeadForm**
- **Model:** Lead
- **Fields:** name, phone, email, buy_or_rent, budget_max, beds, areas, consent_contact
- **Custom Validation:** Phone number cleaning (removes spaces)

### 2. **PropertyUploadForm**
- **Model:** PropertyUpload
- **Fields:** title, description, price_amount, city, area, beds, baths, hero_image
- **Features:**
  - Custom Tailwind CSS styling
  - City dropdown with major US cities
  - Required hero_image
  - Placeholder text guidance

---

## 🎨 Template Tags (myApp/templatetags/extras.py)

Custom Django template filters:

| Filter | Purpose | Example |
|--------|---------|---------|
| `peso` | Format as USD currency | `{{ 3500\|peso }}` → "$3,500" |
| `splitcsv` | Split comma-separated values | `{{ "LA,NYC"\|splitcsv }}` → ['LA', 'NYC'] |
| `strip` | Strip whitespace | `{{ " text "\|strip }}` → "text" |
| `pluralize` | Add 's' if not 1 | `{{ 2\|pluralize }}` → "s" |
| `urlencode` | URL encode | `{{ "LA CA"\|urlencode }}` → "LA%20CA" |
| `split` | Split by delimiter | `{{ "a-b"\|split:"-" }}` → ['a', 'b'] |

---

## 🔄 Complete System Flow Diagrams

### **User Journey 1: Property Search**
```
Homepage → 
  Option A: Traditional search (filters) → results() → Display properties
  Option B: AI prompt → process_ai_search_prompt() → Webhook → results() → Display
→ Click property → property_detail() →
  Chat with bot → property_chat() → simple_answer() → Webhook →
  Submit lead form → lead_submit() → Webhook → Thanks page
```

### **User Journey 2: Property Listing (AI Prompt Path)**
```
listing_choice() → ai_prompt_listing() →
  User enters description + photo →
  Create PropertyUpload (status: processing) →
  process_ai_prompt_with_validation() →
    Extract info with regex →
    Send to OpenAI for validation →
    Identify missing fields →
  processing_listing() (auto-redirects) →
  validation_chat() →
    Display chat interface →
    User provides missing info →
    get_ai_validation_response() (OpenAI) →
    Webhook to CRM →
    Repeat until check_validation_complete() →
  consolidate_property_information() (OpenAI) →
  create_property_from_upload() →
    Create Property object →
    Send listing webhook →
  Redirect to property_detail()
```

### **User Journey 3: Property Listing (Manual Form Path)**
```
listing_choice() → manual_form_listing() →
  User fills comprehensive form →
  Create PropertyUpload with all data →
  validate_manual_form_with_ai() →
    Check completeness →
    If complete: create_property_from_upload() immediately →
    If incomplete: validation_chat() for missing fields →
  property_detail()
```

---

## 🆕 Buyer Homepage Chat System (NEW)

### **Overview**
A conversational property search interface that allows buyers to find properties through natural language chat directly on the homepage, with instant property suggestions and popup quick views.

**Key Differences from Existing Features:**
- **NOT** the property detail page chat (simple_answer bot)
- **NOT** the AI validation chat (for property uploads)
- **NEW** buyer-facing conversational search experience

### **home_chat() View**
- **Location:** `views.py:1462-1524`
- **Route:** `/chat/home/`
- **Method:** POST (HTMX)
- **Purpose:** Process conversational search queries from homepage chat widget

**Functionality:**
1. Receives buyer's natural language message
2. Reuses `process_ai_search_prompt()` to extract parameters
3. Queries properties based on extracted criteria
4. Limits results to top 6 for chat display
5. Generates conversational response via `generate_chat_response()`
6. Sends webhook to CRM (type: "buyer_chat")
7. Returns HTMX partial with chat bubble + property suggestions

**Example Flow:**
```
User: "2 bedroom in LA under $3000 with parking"
→ Extracts: {city: "Los Angeles", beds: 2, price_max: 3000, keywords: ["parking"]}
→ Queries properties
→ Returns: "Perfect! I found 4 great options 2 bedroom in Los Angeles under $3,000. Check these out:"
→ Shows 4 property cards with quick view buttons
```

### **property_modal() View**
- **Location:** `views.py:1549-1577`
- **Route:** `/p/<slug>/modal/`
- **Method:** GET (HTMX)
- **Purpose:** Return property quick view modal for popup preview

**Functionality:**
1. Fetches property by slug
2. Tracks modal view via webhook (type: "property_modal_view")
3. Returns modal HTML partial with property details
4. User can view full details or continue browsing without leaving homepage

### **generate_chat_response() Helper**
- **Location:** `views.py:1527-1546`
- **Purpose:** Generate friendly conversational responses
- **Logic:**
  - Acknowledges search criteria
  - Returns personalized message based on results count
  - Handles no-results gracefully

### **Templates**

**partials/home_chat_suggestions.html**
- Displays AI chat bubble with response text
- Shows grid of up to 6 property suggestions
- Each property card has thumbnail, price, beds/baths
- Click to open modal (HTMX powered)
- "View all results" link to full search page

**partials/property_modal.html**
- Full-screen modal overlay
- Large property image with badges
- Title, location, price
- Key stats grid (beds, baths, sqm, parking)
- Description preview
- Action buttons: "View Full Details" or "Continue Browsing"

**home.html additions:**
- Fixed chat widget button (bottom-right corner)
- Chat panel with greeting message
- HTMX-powered chat form
- Property modal container
- JavaScript for toggle, scroll, and user message display

### **User Experience Flow**

```
Homepage → User clicks chat widget →
  Panel opens with greeting →
  User types: "3 bed house in Miami under $5000" →
  User message appears immediately →
  HTMX sends to /chat/home/ →
  AI response + 6 property suggestions appear →
  User clicks property thumbnail →
  Modal opens with quick view →
  User can view full details OR continue chatting →
  User asks: "show me condos with pool" →
  New suggestions appear in chat →
  Continuous conversation on same page
```

### **Webhooks**

**Buyer Chat Interaction**
```json
{
  "type": "buyer_chat",
  "message": "User's query",
  "results_count": 4,
  "session_id": "session_key",
  "timestamp": "ISO format",
  "extracted_params": {
    "city": "Los Angeles",
    "beds": 2,
    "price_max": 3000
  },
  "utm_source": "",
  "utm_campaign": "",
  "referrer": ""
}
```

**Modal View Tracking**
```json
{
  "type": "property_modal_view",
  "property_id": "uuid",
  "property_slug": "modern-2br-condo",
  "property_title": "Modern 2BR Condo",
  "session_id": "session_key",
  "timestamp": "ISO format",
  "referrer": ""
}
```

---

## 🔌 External Integrations

### **OpenAI GPT-4**
- **API Key:** Stored in `settings.OPENAI_API_KEY` (from environment)
- **Models Used:** `gpt-4`
- **Use Cases:**
  1. Property validation analysis (temperature: 0.1)
  2. Validation chat responses (temperature: 0.3)
  3. Property description consolidation (temperature: 0.7)

### **Katalyst CRM**
- **Protocol:** HTTP POST webhooks
- **Format:** JSON payloads
- **Timeout:** 10 seconds
- **Error Handling:** Logged but non-blocking

---

## 📁 Template Structure

### Main Templates
- `base.html` - Base layout with navigation
- `home.html` - Homepage with featured properties
- `results.html` - Search results page
- `property_detail.html` - Individual property page
- `dashboard.html` - Internal dashboard
- `thanks.html` - Thank you page
- `book.html` - Booking page

### Upload Flow Templates
- `listing_choice.html` - Choose upload method
- `ai_prompt_listing.html` - AI prompt upload form
- `manual_form_listing.html` - Comprehensive manual form
- `upload_listing.html` - Simple upload form
- `processing_listing.html` - Processing status
- `validation_chat.html` - AI validation chat interface

### Partials (HTMX)
- `partials/chat_bubble.html` - Chat message bubble
- `partials/chat_widget.html` - Chat widget
- `partials/lead_form.html` - Lead form partial
- `partials/lead_success.html` - Success message

---

## 🗄️ Database Schema

```
Property
├── id (UUID, PK)
├── slug (unique)
├── title, description
├── price_amount
├── city, area
├── beds, baths, floor_area_sqm
├── parking (boolean)
├── hero_image (URL)
├── badges
└── created_at

Lead
├── id (UUID, PK)
├── name, phone, email
├── buy_or_rent
├── budget_max, beds
├── areas, interest_ids
├── utm_source, utm_campaign, referrer
└── created_at

PropertyUpload
├── id (UUID, PK)
├── property (FK to Property, nullable)
├── status (choice field)
├── title, description, price_amount, etc.
├── hero_image (ImageField)
├── ai_validation_result (JSON)
├── missing_fields (JSON)
├── validation_chat_history (JSON)
├── consolidated_information
└── created_at, updated_at
```

---

## 🎯 Key System Characteristics

### **Strengths:**
1. **Dual-path upload** - Flexible for different user preferences
2. **AI-powered validation** - Ensures listing quality
3. **Conversational UX** - Chat-based missing field collection
4. **CRM integration** - Full tracking of user interactions
5. **HTMX** - Fast, modern UX without heavy JS
6. **Comprehensive checklist** - 9-section real estate standard

### **Current Technologies:**
- **Backend:** Django 4.2+
- **Database:** SQLite (dev), upgradeable to PostgreSQL
- **AI:** OpenAI GPT-4
- **Frontend:** Tailwind CSS, HTMX
- **Deployment:** Railway
- **Media:** Local file storage (upgradeable to S3)

### **Environment Variables:**
- `OPENAI_API_KEY` - OpenAI API key
- `SECRET_KEY` - Django secret key (hardcoded in dev, should be env var in prod)

---

## 🔐 Admin Interface

Registered models in Django Admin:
1. **PropertyAdmin** - List, filter, search properties
2. **LeadAdmin** - Manage leads
3. **PropertyUploadAdmin** - Monitor upload process, view AI results

---

## 📊 Analytics & Tracking

Every major user interaction sends a webhook:
- Lead submissions
- Property chat messages
- AI prompt searches
- Property listings created
- Validation chat interactions

Tracking fields captured:
- `utm_source`, `utm_campaign` (from cookies/GET params)
- `referrer` (HTTP_REFERER)
- `session_id` (Django session key)
- `ip_address`, `user_agent` (for chat)
- `timestamp` (ISO format)

---

## 🚀 System Scalability Notes

**Current State:** Development-ready, single-server deployment

**Production Considerations:**
1. Move SQLite → PostgreSQL
2. Add Celery for async AI processing
3. Implement caching (Redis)
4. Move media to S3/CloudFlare
5. Add rate limiting
6. Environment-based settings
7. Monitoring/logging (Sentry)

---

This documentation represents the complete functional architecture of your real estate platform as of the current codebase state.

