# PropertyHub - Real Estate Listing Platform

## Overview
PropertyHub is a Django-based real estate property listing application with AI-powered search capabilities. The platform allows users to search for properties using natural language prompts, upload listings, and interact with a chat widget for inquiries.

## Project Architecture

### Technology Stack
- **Backend**: Django 5.1.2 (Python web framework)
- **Database**: SQLite (development), PostgreSQL support available
- **Storage**: Cloudinary (media files)
- **AI Integration**: Webhook-based AI chat (Katalyst CRM), OpenAI API (for smart property search)
- **Frontend**: HTML/Tailwind CSS/JavaScript/HTMX
- **Payment**: Stripe integration
- **Real-time**: Django Channels (WebSocket support)

### Key Features
1. **Webhook-Powered AI Chatbox**: Interactive conversational AI that transforms the search form into a real-time chatbox
2. **AI-Powered Property Search**: Natural language property search using OpenAI
3. **Property Listings**: Browse, filter, and view detailed property information
4. **Upload System**: Property upload with AI-assisted listing generation
5. **Chat Widget**: Interactive chat for buyer inquiries
6. **Lead Management**: Capture and manage property leads
7. **Webhook Integration**: External system notifications via Katalyst CRM

## Project Structure
```
myProject/              # Main Django project
├── settings.py        # Configuration
├── urls.py           # URL routing
└── wsgi.py/asgi.py   # Server interfaces

myApp/                 # Main application
├── models.py         # Database models (Property, Lead, PropertyUpload)
├── views.py          # View logic
├── forms.py          # Form definitions
├── webhook.py        # Webhook handlers
├── templates/        # HTML templates
├── static/          # Static assets
└── management/      # Custom Django commands

media/                # User uploaded files (migrated to Cloudinary)
staticfiles/         # Collected static files
```

## Environment Setup

### Required Secrets
The application requires the following API keys (optional for basic functionality):

1. **OPENAI_API_KEY**: For AI-powered property search
2. **CLOUDINARY_CLOUD_NAME**: For media storage
3. **CLOUDINARY_API_KEY**: For media storage
4. **CLOUDINARY_API_SECRET**: For media storage

### Configuration
- **Port**: 5000 (configured for Replit)
- **Allowed Hosts**: Set to `*` for Replit compatibility
- **CSRF Trusted Origins**: Configured for Replit domains
- **Static Files**: WhiteNoise for serving static files
- **Media Files**: Cloudinary for uploads

## Development Workflow

### Running the Server
The Django development server runs automatically via the "Django Server" workflow on port 5000.

### Database
- Migrations are already applied
- SQLite database (`db.sqlite3`) contains sample data
- Models include: Property, Lead, PropertyUpload

### Static Files
Static files are collected to `staticfiles/` directory and served via WhiteNoise.

## Recent Changes
- **2025-10-10**: Webhook-Powered Chatbox Implementation
  - Added `init_webhook_chat` view to transform search form into chatbox
  - Added `webhook_chat` view for ongoing conversation messages
  - Created chatbox interface template with HTMX integration
  - Webhook URL: `https://katalyst-crm.fly.dev/webhook-test/ca05d7c5-984c-4d95-8636-1ed3d80f5545` (test endpoint)
  - Webhook payload: `{"message": "user message", "sessionID": "session_key"}`
  - Webhook response: Expects `{"Response": "AI response text"}`
  - All responses come ONLY from webhook - no fallback AI responses
  - Implemented session-based chat history with sessionID for memory
  - Modified home.html to use webhook chatbox instead of traditional search results
  - User flow: Enter description → Click "Find My Perfect Home" → Form transforms to chatbox → AI conversation begins

- **2025-10-10**: Initial Replit setup
  - Configured Django settings for Replit environment
  - Set ALLOWED_HOSTS to support Replit proxy
  - Updated CSRF trusted origins
  - Installed all dependencies from requirements.txt
  - Configured workflow for port 5000
  - Collected static files

## Deployment Notes
- The application is configured for deployment on Replit
- Static files use WhiteNoise for production serving
- Media files should use Cloudinary (requires API keys)
- For production, set DEBUG=False and configure proper SECRET_KEY

## Notes
- The Tailwind CSS is loaded via CDN (development only)
- Cloudinary integration requires API credentials to be set
- OpenAI features require API key configuration
- Favicon is not configured (minor 404 error)
