# PropertyHub - Real Estate Listing Platform

## Overview
PropertyHub is a Django-based real estate property listing application with AI-powered search capabilities. The platform allows users to search for properties using natural language prompts, upload listings, and interact with a chat widget for inquiries.

## Project Architecture

### Technology Stack
- **Backend**: Django 5.1.2 (Python web framework)
- **Database**: SQLite (development), PostgreSQL support available
- **Storage**: Cloudinary (media files)
- **AI Integration**: OpenAI API (for smart property search)
- **Frontend**: HTML/Tailwind CSS/JavaScript
- **Payment**: Stripe integration
- **Real-time**: Django Channels (WebSocket support)

### Key Features
1. **AI-Powered Property Search**: Natural language property search using OpenAI
2. **Property Listings**: Browse, filter, and view detailed property information
3. **Upload System**: Property upload with AI-assisted listing generation
4. **Chat Widget**: Interactive chat for buyer inquiries
5. **Lead Management**: Capture and manage property leads
6. **Webhook Integration**: External system notifications

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
