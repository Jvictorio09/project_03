# System Flow Diagrams

## 🎯 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  (Django Templates + Tailwind CSS + HTMX)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DJANGO VIEWS                             │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   Search     │  Property    │    Lead      │   Upload     │ │
│  │   System     │    Chat      │   Capture    │   System     │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │   OpenAI    │  │  Katalyst   │  │   SQLite    │
    │   GPT-4     │  │    CRM      │  │  Database   │
    │    API      │  │  Webhooks   │  │             │
    └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 🔍 Flow 1: Property Search & Discovery

### Traditional Search Flow
```
┌──────────┐
│  User    │
│ Homepage │
└────┬─────┘
     │
     ▼
┌─────────────────────────────┐
│ Fills search filters:       │
│ - City (dropdown)           │
│ - Beds (min)                │
│ - Price max                 │
│ - Keyword search            │
└────┬────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ results() view              │
│ - Parse query params        │
│ - Filter with Q objects     │
│ - Search: title, desc, city │
└────┬────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ Display results.html        │
│ - Show filtered properties  │
│ - Show count                │
└─────────────────────────────┘
```

### AI Prompt Search Flow
```
┌──────────┐
│  User    │
│ Homepage │
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Types natural language:             │
│ "2 bedroom in LA under $3000"       │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ process_ai_search_prompt()          │
│                                     │
│ EXTRACTS:                           │
│ ├─ City: regex + city list match   │
│ ├─ Beds: regex (\d+)\s*bed          │
│ ├─ Price: regex \$([0-9,]+)         │
│ ├─ Buy/Rent: keyword matching       │
│ └─ Keywords: condo, pool, gym, etc. │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Apply filters to Property QuerySet │
│ - city__icontains                   │
│ - beds__gte                         │
│ - price_amount__lte                 │
│ - keyword searches in desc/badges   │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ send_prompt_search_webhook()        │
│ - Send to Katalyst CRM              │
│ - Track: prompt, results, session   │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Display results.html                │
│ - Show "AI Search" badge            │
│ - Show original prompt              │
└─────────────────────────────────────┘
```

---

## 💬 Flow 2: Property Chat System

```
┌─────────────────────┐
│ User on Property    │
│ Detail Page         │
└────┬────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Sees chat widget                 │
│ Types: "How much is rent?"       │
└────┬─────────────────────────────┘
     │
     ▼ (HTMX POST)
┌──────────────────────────────────┐
│ property_chat() view             │
│ - Receive message                │
│ - Get property object            │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ simple_answer(property, message) │
│                                  │
│ KEYWORD MATCHING:                │
│ ├─ "price/rent" → Price response │
│ ├─ "bed" → Bedroom count         │
│ ├─ "bath" → Bathroom count       │
│ ├─ "size" → Floor area           │
│ ├─ "park" → Parking status       │
│ ├─ "where" → Location + Maps URL │
│ ├─ "available" → Contact agent   │
│ └─ else → Fallback response      │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ send_property_chat_webhook()     │
│ - Type: "Property_inquiry"       │
│ - Send message + response        │
│ - Property context               │
│ - Session tracking               │
└────┬─────────────────────────────┘
     │
     ▼ (HTMX response)
┌──────────────────────────────────┐
│ Return chat_bubble.html partial  │
│ - Role: "assistant"              │
│ - Text: response                 │
│ - Time: "now"                    │
└──────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ HTMX swaps into chat container   │
│ User sees response instantly     │
└──────────────────────────────────┘
```

---

## 📋 Flow 3: Lead Capture System

```
┌────────────────────┐
│ User interested    │
│ in property        │
└────┬───────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Fills lead form:                 │
│ - Name (required)                │
│ - Phone (required, cleaned)      │
│ - Email (optional)               │
│ - Buy or Rent                    │
│ - Budget max                     │
│ - Beds                           │
│ - Areas of interest              │
│ - Consent checkbox               │
└────┬─────────────────────────────┘
     │
     ▼ (POST via HTMX or full form)
┌──────────────────────────────────┐
│ lead_submit() view               │
│ - Validate LeadForm              │
│ - Clean phone (remove spaces)    │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Enhance with tracking data:      │
│ - utm_source (from cookie/GET)   │
│ - utm_campaign (from cookie/GET) │
│ - referrer (HTTP_REFERER)        │
│ - interest_ids (property IDs)    │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Save Lead to database            │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ send_chat_inquiry_webhook()      │
│ - Type: "chat_inquiry"           │
│ - Full lead data                 │
│ - Tracking info                  │
│ - Session ID                     │
│ - Timestamp                      │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ If HTMX request:                 │
│   Return lead_success.html       │
│ Else:                            │
│   Redirect to /thanks?lead={id}  │
└──────────────────────────────────┘
```

---

## 🤖 Flow 4: AI Property Upload & Validation (Complete)

### Path A: AI Prompt Upload

```
START: User visits /listing-choice/

┌────────────────────────┐
│ listing_choice() view  │
│ Shows 2 options        │
└────┬───────────────────┘
     │
     ▼ (User clicks "AI Prompt Upload")
┌────────────────────────────────────────┐
│ ai_prompt_listing() view               │
│ Shows form:                            │
│ - Property description (textarea)      │
│ - Additional info (textarea)           │
│ - Hero image (file upload)             │
└────┬───────────────────────────────────┘
     │
     ▼ (User submits)
┌────────────────────────────────────────┐
│ Create PropertyUpload:                 │
│ - title: "AI-Generated Listing"        │
│ - description: user's prompt           │
│ - hero_image: uploaded file            │
│ - status: 'processing'                 │
└────┬───────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ process_ai_prompt_with_validation()                     │
│                                                         │
│ 1. Extract basic info with regex:                      │
│    ├─ extract_basic_info_from_description()            │
│    │  ├─ Price: \$([0-9,]+)                            │
│    │  ├─ Beds: (\d+)\s*bed                             │
│    │  ├─ Baths: (\d+)\s*bath                           │
│    │  ├─ City: match against US city list              │
│    │  └─ Title: first sentence                         │
│    │                                                    │
│ 2. Send to OpenAI for validation:                      │
│    ├─ Model: gpt-4                                     │
│    ├─ System prompt: Real estate checklist             │
│    ├─ User prompt: Full description                    │
│    └─ Temperature: 0.3                                 │
│                                                         │
│ 3. Store results:                                      │
│    ├─ Update upload with extracted info                │
│    ├─ ai_validation_result = AI analysis               │
│    ├─ missing_fields = generate_missing_fields_list()  │
│    └─ validation_chat_history = Initial AI message     │
│                                                         │
│ 4. Update status:                                      │
│    └─ status: 'validation'                             │
└────┬────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│ Redirect to processing_listing()       │
│ - Shows "Processing..." briefly        │
│ - Auto-redirects to validation_chat()  │
└────┬───────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ validation_chat() view                                  │
│                                                         │
│ DISPLAYS:                                               │
│ ├─ Chat interface                                       │
│ ├─ Completion percentage (0-100%)                       │
│ ├─ Validation status (9 sections)                       │
│ └─ Missing fields list                                  │
│                                                         │
│ Initial AI message already present:                     │
│ "I've identified {N} critical areas..."                 │
└────┬────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│ USER INTERACTION LOOP                  │
└────┬───────────────────────────────────┘
     │
     ▼ (User types response)
┌─────────────────────────────────────────────────────────┐
│ validation_chat() POST handler                          │
│ 1. Add user message to chat_history                     │
│ 2. Call get_ai_validation_response()                    │
└────┬────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ get_ai_validation_response()                            │
│                                                         │
│ CONTEXT BUILDING:                                       │
│ ├─ Current property data                                │
│ ├─ Missing fields list                                  │
│ ├─ Question index (count of user messages)              │
│ └─ Full chat history                                    │
│                                                         │
│ OPENAI CALL:                                            │
│ ├─ Model: gpt-4                                         │
│ ├─ Temperature: 0.3                                     │
│ ├─ System prompt: Comprehensive checklist guide         │
│ │  - Ask ONE specific field at a time                   │
│ │  - Provide format examples                            │
│ │  - Acknowledge info and move to next                  │
│ │  - Reference 9-section checklist                      │
│ └─ Max tokens: 800                                      │
│                                                         │
│ FALLBACK (if API fails):                                │
│ └─ get_specific_fallback_response()                     │
│    - Pre-written specific questions for each field      │
│    - Keyword-based response matching                    │
│    - Systematic progression through missing fields      │
└────┬────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Add AI response to chat_history                      │
│ 4. Save updated PropertyUpload                          │
└────┬────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ send_chat_inquiry_webhook()                             │
│ - Type: "chat_inquiry"                                  │
│ - Message: user's response                              │
│ - Property context from upload                          │
│ - Validation progress tracking                          │
└────┬────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ check_validation_complete()                             │
│                                                         │
│ CHECKS:                                                 │
│ ├─ Has basic required: title, price, city?             │
│ │  → If yes: COMPLETE                                   │
│ │                                                       │
│ └─ Has 3+ user messages in chat?                        │
│    → If yes: COMPLETE (substantial engagement)          │
└────┬────────────────────────────────────────────────────┘
     │
     ├─ NOT COMPLETE → Loop back to user interaction
     │
     ▼ COMPLETE!
┌─────────────────────────────────────────────────────────┐
│ consolidate_property_information()                      │
│                                                         │
│ CONSOLIDATION PROCESS:                                  │
│ ├─ Collect all upload data                              │
│ ├─ Extract all user responses from chat                 │
│ ├─ Combine into comprehensive dataset                   │
│ │                                                       │
│ ├─ Send to OpenAI:                                      │
│ │  ├─ Model: gpt-4                                      │
│ │  ├─ Temperature: 0.7 (creative copywriting)           │
│ │  ├─ Prompt: Create professional listing (200-300w)    │
│ │  └─ Style: Compelling, structured, buyer-focused      │
│ │                                                       │
│ └─ Store result in consolidated_information             │
└────┬────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ create_property_from_upload()                           │
│                                                         │
│ PROPERTY CREATION:                                      │
│ ├─ Generate unique slug                                 │
│ ├─ Create Property object:                              │
│ │  ├─ title: from upload                                │
│ │  ├─ description: consolidated_information             │
│ │  ├─ price_amount, city, area, beds, baths            │
│ │  ├─ hero_image: upload.hero_image.url                 │
│ │  └─ badges: "AI-Validated, Complete Listing"         │
│ │                                                       │
│ ├─ Link upload.property = created Property              │
│ └─ Update upload.status = 'complete'                    │
└────┬────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ send_property_listing_webhook()                         │
│ - Type: "property_listing"                              │
│ - Full property data                                    │
│ - Validation results                                    │
│ - Missing fields (what was filled)                      │
│ - Consolidated information                              │
│ - Source: "ai_validation"                               │
└────┬────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ Redirect to property_detail(property.slug)              │
│ → User sees their published listing!                    │
└─────────────────────────────────────────────────────────┘

END: Property is live on the platform
```

### Path B: Manual Form Upload

```
START: User visits /listing-choice/

┌────────────────────────┐
│ listing_choice() view  │
└────┬───────────────────┘
     │
     ▼ (User clicks "Manual Form Upload")
┌─────────────────────────────────────────────────────────┐
│ manual_form_listing() view                              │
│                                                         │
│ Shows comprehensive form:                               │
│ ├─ BASIC INFO: title, description, price, beds, baths   │
│ ├─ LOCATION: street address, city, state, zip, schools  │
│ ├─ BUILDING: property type, sqft, lot size, year built  │
│ ├─ FEATURES: kitchen, outdoor, amenities, special       │
│ ├─ FINANCIAL: HOA fees, taxes, utilities, financing     │
│ └─ MEDIA: hero image                                    │
└────┬────────────────────────────────────────────────────┘
     │
     ▼ (User submits comprehensive form)
┌─────────────────────────────────────────────────────────┐
│ Create PropertyUpload:                                  │
│ ├─ Basic fields: title, description, price, etc.        │
│ └─ Store comprehensive data in ai_validation_result:    │
│    {                                                    │
│      property_type, listing_status, street_address,     │
│      state, zip_code, school_district, sqft, lot_size,  │
│      year_built, parking, kitchen_features,             │
│      outdoor_features, amenities, hoa_fees, taxes, etc. │
│    }                                                    │
│ - status: 'processing'                                  │
└────┬────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ validate_manual_form_with_ai()                          │
│                                                         │
│ LIGHT VALIDATION:                                       │
│ ├─ Check critical fields:                               │
│ │  ├─ Title → provided_fields or missing_critical       │
│ │  ├─ Price → provided_fields or missing_critical       │
│ │  ├─ City → provided_fields or missing_critical        │
│ │  └─ Street Address → provided_fields or missing       │
│ │                                                       │
│ ├─ Check comprehensive fields:                          │
│ │  ├─ property_type, beds, baths, sqft, year_built     │
│ │  ├─ kitchen_features, outdoor_features, amenities     │
│ │  └─ Count towards completeness_score                  │
│ │                                                       │
│ ├─ Create validation_result:                            │
│ │  ├─ status: 'comprehensive' or 'needs_improvement'    │
│ │  ├─ provided_fields: []                               │
│ │  ├─ missing_critical: []                              │
│ │  ├─ completeness_score: % (out of 20 key fields)      │
│ │  └─ recommendations: []                               │
│ │                                                       │
│ └─ Update upload:                                       │
│    ├─ ai_validation_result = validation_result          │
│    ├─ missing_fields = missing_critical                 │
│    └─ status = 'validation' OR 'complete'               │
└────┬────────────────────────────────────────────────────┘
     │
     ├─ Has missing critical?
     │  ├─ YES → status='validation'
     │  │        → Redirect to validation_chat()
     │  │        → User provides missing info
     │  │        → (Same chat flow as AI prompt path)
     │  │
     │  └─ NO → status='complete'
     │           → Call create_property_from_upload() immediately
     │           → Skip validation chat
     │
     ▼ (If complete)
┌─────────────────────────────────────────────────────────┐
│ create_property_from_upload()                           │
│ → Creates Property immediately                          │
│ → Sends webhook                                         │
│ → Redirect to property_detail()                         │
└─────────────────────────────────────────────────────────┘

END: Property is live (faster if form is complete)
```

### Path C: Simple Upload

```
START: User visits /upload-listing/

┌────────────────────────────────────────┐
│ upload_listing() view                  │
│ Shows PropertyUploadForm:              │
│ - title, description, price            │
│ - city (dropdown), area                │
│ - beds, baths                          │
│ - hero_image                           │
└────┬───────────────────────────────────┘
     │
     ▼ (User submits)
┌────────────────────────────────────────┐
│ Create PropertyUpload                  │
│ - status: 'processing'                 │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│ validate_property_with_ai()            │
│ (Same as AI prompt path validation)    │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│ Redirect to processing_listing()       │
│ → Auto-redirect to validation_chat()   │
│ → (Same flow as AI prompt)             │
└────────────────────────────────────────┘

END: Goes through full validation chat
```

---

## 🎛️ Dashboard Flow

```
┌─────────────────────┐
│ Internal user       │
│ visits /dashboard   │
└────┬────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ dashboard() view                 │
│                                  │
│ PARSE QUERY PARAMS:              │
│ ├─ q (search query)              │
│ ├─ city (filter)                 │
│ ├─ sort (new, price, beds)       │
│ ├─ page (pagination)             │
│ └─ per (items per page: 12-48)   │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Build QuerySet:                  │
│ ├─ Filter by search query        │
│ ├─ Filter by city                │
│ ├─ Order by sort option          │
│ └─ Paginate                      │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Get metadata:                    │
│ ├─ Distinct cities list          │
│ └─ Total count                   │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Render dashboard.html            │
│ - Property grid                  │
│ - Search/filter controls         │
│ - Pagination                     │
│ - Sort options                   │
└──────────────────────────────────┘
```

---

## 🔔 Webhook Event Types

```
┌─────────────────────────────────────────────────┐
│              WEBHOOK TRIGGERS                   │
└─────────────────────────────────────────────────┘

1. "chat_inquiry"
   ├─ Lead form submission (lead_submit)
   └─ Validation chat interactions (validation_chat)

2. "Property_inquiry"  
   ├─ Property detail page chat (property_chat)
   └─ AI prompt search (results with ai_prompt)

3. "property_listing"
   └─ New property created (create_property_from_upload)

All webhooks include:
├─ timestamp (ISO format)
├─ session_id (Django session key)
├─ tracking (utm_source, utm_campaign, referrer)
└─ type-specific payload
```

---

## 🆕 Flow 5: Buyer Homepage Chat System (NEW)

### Conversational Property Search with Quick View Modals

```
START: User on Homepage

┌────────────────────────────────────┐
│ User sees chat widget              │
│ (fixed bottom-right button)        │
└────┬───────────────────────────────┘
     │
     ▼ (Clicks chat button)
┌────────────────────────────────────┐
│ Chat panel opens                   │
│ - Shows greeting from AI           │
│ - Input field ready                │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────┐
│ User types conversational query:                   │
│ "2 bedroom condo in LA under $3500 with parking"   │
└────┬───────────────────────────────────────────────┘
     │
     ▼ (HTMX POST to /chat/home/)
┌────────────────────────────────────────────────────┐
│ home_chat() view                                   │
│                                                    │
│ 1. Receive message                                 │
│ 2. Process with process_ai_search_prompt()         │
│    ├─ Extract city: "Los Angeles"                  │
│    ├─ Extract beds: 2                              │
│    ├─ Extract price_max: 3500                      │
│    └─ Extract keywords: ["condo", "parking"]       │
│                                                    │
│ 3. Query properties:                               │
│    qs = Property.objects.all()                     │
│    ├─ Filter by city                               │
│    ├─ Filter beds >= 2                             │
│    ├─ Filter price <= 3500                         │
│    └─ Filter keywords in title/desc/badges         │
│                                                    │
│ 4. Limit to top 6 results                          │
│                                                    │
│ 5. Generate response:                              │
│    generate_chat_response()                        │
│    → "Perfect! I found 4 great options..."         │
│                                                    │
│ 6. Send webhook:                                   │
│    send_chat_inquiry_webhook()                     │
│    - type: "buyer_chat"                            │
│    - message, results_count, extracted_params      │
└────┬───────────────────────────────────────────────┘
     │
     ▼ (Return HTMX partial)
┌────────────────────────────────────────────────────┐
│ partials/home_chat_suggestions.html                │
│                                                    │
│ RENDERS:                                           │
│ ├─ AI chat bubble with response text              │
│ └─ Property suggestion cards (up to 6):            │
│    ┌────────────────────────────────┐             │
│    │ [Thumbnail] Property Title     │             │
│    │             $3,500             │             │
│    │             2 bed • 2 bath     │             │
│    │             [👁 Quick View]     │             │
│    └────────────────────────────────┘             │
│    (Click opens modal via HTMX)                    │
│                                                    │
│ ├─ "View all results" link                         │
└────┬───────────────────────────────────────────────┘
     │
     ▼ (HTMX swaps into chat-messages div)
┌────────────────────────────────────────────────────┐
│ Chat updates instantly:                            │
│ - User message bubble appears                      │
│ - AI response bubble appears                       │
│ - 4 property cards displayed                       │
│ - Chat auto-scrolls to bottom                      │
└────┬───────────────────────────────────────────────┘
     │
     ├─ OPTION A: User clicks property thumbnail
     │  │
     │  ▼ (HTMX GET to /p/<slug>/modal/)
     │  ┌────────────────────────────────────────────┐
     │  │ property_modal() view                      │
     │  │                                            │
     │  │ 1. Fetch property by slug                  │
     │  │ 2. Track modal view:                       │
     │  │    send_property_chat_webhook()            │
     │  │    - type: "property_modal_view"           │
     │  │                                            │
     │  │ 3. Return partials/property_modal.html     │
     │  └────┬───────────────────────────────────────┘
     │       │
     │       ▼ (HTMX swaps into modal container)
     │  ┌────────────────────────────────────────────┐
     │  │ Modal appears:                             │
     │  │ - Full-screen overlay                      │
     │  │ - Large property image                     │
     │  │ - Title, price, location                   │
     │  │ - Key stats grid                           │
     │  │ - Description preview                      │
     │  │ - Action buttons:                          │
     │  │   ├─ "View Full Details" → /property/slug/ │
     │  │   └─ "Continue Browsing" → Close modal     │
     │  └────┬───────────────────────────────────────┘
     │       │
     │       ├─ User clicks "View Full Details"
     │       │  → Navigate to property_detail page
     │       │
     │       └─ User clicks "Continue Browsing"
     │          → Modal closes, stays on homepage
     │
     ├─ OPTION B: User asks follow-up question
     │  │
     │  ▼
     │  User types: "show me ones with a pool"
     │  → Loop back to home_chat()
     │  → New suggestions appear in chat
     │  → Continuous conversation
     │
     └─ OPTION C: User clicks "View all results"
        → Navigate to /list?ai_prompt=...
        → Full search results page

END: User continues browsing or exits
```

### Key Interactions Summary

```
┌─────────────────────────────────────────────────┐
│          Homepage Chat Widget Flow              │
└─────────────────────────────────────────────────┘

Chat Widget Button → Toggle Panel → Type Message →
  ↓
home_chat() → process_ai_search_prompt() →
  ↓
Query Properties → Generate Response →
  ↓
Send Webhook → Return Suggestions →
  ↓
Display in Chat → Click Property Card →
  ↓
property_modal() → Show Quick View →
  ↓
  ├─ View Full Details (navigate away)
  ├─ Continue Browsing (stay on page)
  └─ Ask Another Question (loop back)


STAYS ON HOMEPAGE THROUGHOUT!
No page reloads, all HTMX-powered
```

---

## 📊 Data Model Relationships

```
┌──────────────────┐
│   Property       │ ◄─────────┐
│  (Final Listing) │            │ OneToOne
└──────────────────┘            │
                                │
                         ┌──────────────────┐
                         │  PropertyUpload  │
                         │  (Upload Process)│
                         └──────────────────┘

┌──────────────────┐
│      Lead        │
│ (Customer Info)  │
│                  │
│ interest_ids ────┼──► (References Property IDs)
└──────────────────┘
```

---

This documentation provides complete visual flows for every major system function!

