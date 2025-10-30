# 🏠 KaTek Real Estate Platform

A comprehensive Django-based real estate platform with AI-powered property search, automated lead management, and N8N integration for seamless workflow automation.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Django 5.1+
- Node.js (for Tailwind CSS)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd project_03

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python run_local.py
```

### Access the Application
- **Homepage:** http://127.0.0.1:8000
- **Admin Panel:** http://127.0.0.1:8000/admin
- **Dashboard:** http://127.0.0.1:8000/dashboard

## 📚 Documentation

**All documentation has been organized in the `documentations/` folder:**

- **[📖 Complete Documentation](documentations/README.md)** - Comprehensive documentation index
- **[🚀 Setup Guide](documentations/setup/SETUP_GUIDE.md)** - Complete setup instructions
- **[🏗️ System Architecture](documentations/architecture/SYSTEM_FLOWS.md)** - User journey flows
- **[🤖 N8N Integration](documentations/architecture/N8N_INTEGRATION_ARCHITECTURE.md)** - Automation workflows
- **[🚀 Deployment Guide](documentations/deployment/DEPLOYMENT_READY.md)** - Production deployment

### Quick Documentation Links
- **Setup Issues?** → [documentations/setup/](documentations/setup/)
- **Deployment Problems?** → [documentations/deployment/](documentations/deployment/)
- **Feature Questions?** → [documentations/features/](documentations/features/)
- **System Understanding?** → [documentations/architecture/](documentations/architecture/)
- **Bug Fixes?** → [documentations/troubleshooting/](documentations/troubleshooting/)
- **Dashboard & n8n Migration** → [documentations/IMPLEMENTATION_NOTES.md](documentations/IMPLEMENTATION_NOTES.md)
- **API Contracts** → [documentations/API_CONTRACTS_DASHBOARD.md](documentations/API_CONTRACTS_DASHBOARD.md)
- **n8n Workflows** → [documentations/N8N_WORKFLOWS.md](documentations/N8N_WORKFLOWS.md)

## ✨ Key Features

- **🤖 AI-Powered Search** - Natural language property search
- **💬 Interactive Chat** - Property-specific AI chat assistance
- **📋 Smart Lead Capture** - Automated lead scoring and CRM integration
- **🏠 Property Upload** - AI-assisted property listing creation
- **🔄 N8N Automation** - Workflow automation and integrations
- **📱 Responsive Design** - Mobile-first Tailwind CSS design
- **🔐 Google OAuth** - Secure authentication
- **☁️ Cloudinary Integration** - Image storage and optimization

## 🏗️ Architecture

### Frontend
- **Django Templates** with Tailwind CSS
- **HTMX** for dynamic interactions
- **Responsive Design** for all devices

### Backend
- **Django 5.1** with SQLite database
- **OpenAI GPT-4** for AI features
- **N8N** for workflow automation
- **Cloudinary** for media storage

### Integrations
- **Google OAuth** for authentication
- **HubSpot/Salesforce** for CRM
- **Resend** for email services
- **RentCast** for market data

## 🎯 User Journeys

### Property Buyers
1. **Search Properties** - AI-powered or traditional search
2. **View Details** - Interactive property pages
3. **Chat with AI** - Get instant property information
4. **Submit Lead** - Contact form with preferences
5. **Get Follow-up** - Automated CRM integration

### Property Sellers
1. **Upload Property** - AI-assisted or manual form
2. **AI Validation** - Interactive chat to complete details
3. **Property Goes Live** - Automatic publication
4. **Lead Management** - Track inquiries and conversions

## 🔧 Development

### Running Locally
```bash
# Use the provided script (recommended)
python run_local.py

# Or manually
python manage.py runserver
```

### Environment Setup
Copy `documentations/setup/ENV_EXAMPLE.txt` to `.env` and configure:
- OpenAI API key
- Cloudinary credentials
- Google OAuth credentials
- Database settings

## 📊 Project Structure

```
project_03/
├── 📁 myApp/                    # Main Django application
├── 📁 myProject/               # Django project settings
├── 📁 static/                  # Static files (CSS, JS)
├── 📁 media/                   # User uploaded files
├── 📁 documentations/          # 📚 All documentation organized
│   ├── setup/                  # Setup guides
│   ├── deployment/             # Deployment guides
│   ├── architecture/           # System architecture
│   ├── features/               # Feature documentation
│   └── troubleshooting/        # Debug guides
├── 📄 manage.py                # Django management
├── 📄 requirements.txt         # Python dependencies
└── 📄 db.sqlite3              # Database
```

## 🤝 Contributing

1. **Documentation** - All docs are in `documentations/` folder
2. **Code Standards** - Follow Django best practices
3. **Testing** - Run tests before submitting changes
4. **Issues** - Check `documentations/troubleshooting/` first

## 📞 Support

- **Documentation:** [documentations/README.md](documentations/README.md)
- **Quick Reference:** [documentations/QUICK_REFERENCE.md](documentations/QUICK_REFERENCE.md)
- **Troubleshooting:** [documentations/troubleshooting/](documentations/troubleshooting/)

---

**Built with ❤️ using Django, Tailwind CSS, and AI automation**
"# project_03" 
