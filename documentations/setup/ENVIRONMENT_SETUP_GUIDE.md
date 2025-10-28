# 🔧 Environment Variables Setup Guide

## ✅ What I've Added

I've configured your Django settings to use environment variables from a `.env` file:

### **Updated `myProject/settings.py`:**
- ✅ **Added `load_dotenv()`** to load environment variables
- ✅ **Added OpenAI configuration** from env vars
- ✅ **Added Cloudinary configuration** from env vars
- ✅ **Organized API keys section** with clear comments

---

## 📋 **Environment Variables Added**

### **OpenAI Configuration:**
```python
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
```

### **Cloudinary Configuration:**
```python
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')
CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', '')
```

---

## 🔑 **Setup Steps**

### **1. Create `.env` File**
Create a `.env` file in your project root (same level as `manage.py`):

```bash
# In your project root
touch .env
```

### **2. Add Your Environment Variables**
Copy the contents from `ENV_EXAMPLE.txt` to your `.env` file and fill in your actual values:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your-actual-cloud-name
CLOUDINARY_API_KEY=your-actual-api-key
CLOUDINARY_API_SECRET=your-actual-api-secret

# Django Configuration
SECRET_KEY=your-django-secret-key-here
DEBUG=True
```

### **3. Get Your API Keys**

#### **OpenAI API Key:**
1. Go to: https://platform.openai.com/api-keys
2. Create new secret key
3. Copy the key (starts with `sk-`)

#### **Cloudinary Credentials:**
1. Go to: https://cloudinary.com/console
2. Sign up/login to your account
3. Go to Dashboard
4. Copy:
   - **Cloud name** (from "Account Details")
   - **API Key** (from "Account Details")
   - **API Secret** (from "Account Details")

---

## 🎯 **Usage in Your Code**

### **Accessing Environment Variables:**

```python
from django.conf import settings

# OpenAI
openai_api_key = settings.OPENAI_API_KEY

# Cloudinary
cloud_name = settings.CLOUDINARY_CLOUD_NAME
api_key = settings.CLOUDINARY_API_KEY
api_secret = settings.CLOUDINARY_API_SECRET
```

### **Example Usage in Views:**

```python
import openai
from django.conf import settings

def my_ai_function():
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    # Use OpenAI API...
```

### **Example Cloudinary Usage:**

```python
import cloudinary
from django.conf import settings

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)
```

---

## 🔒 **Security Best Practices**

### **1. Never Commit `.env` File**
Make sure `.env` is in your `.gitignore`:

```gitignore
# Environment variables
.env
.env.local
.env.production
```

### **2. Use Different Keys for Different Environments**
- **Development:** `.env` file with test keys
- **Production:** Environment variables set on server
- **Staging:** Separate `.env.staging` file

### **3. Rotate Keys Regularly**
- Change API keys periodically
- Use different keys for different projects
- Monitor API usage

---

## 🧪 **Testing Configuration**

### **Test Script:**
Create a test script to verify your environment variables:

```python
# test_env.py
import os
from dotenv import load_dotenv

load_dotenv()

print("Environment Variables Test:")
print(f"OpenAI API Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
print(f"Cloudinary Cloud Name: {'✅ Set' if os.getenv('CLOUDINARY_CLOUD_NAME') else '❌ Missing'}")
print(f"Cloudinary API Key: {'✅ Set' if os.getenv('CLOUDINARY_API_KEY') else '❌ Missing'}")
print(f"Cloudinary API Secret: {'✅ Set' if os.getenv('CLOUDINARY_API_SECRET') else '❌ Missing'}")
```

Run it:
```bash
python test_env.py
```

---

## 🚀 **Django Management Command**

You can also create a Django command to test your configuration:

```python
# myApp/management/commands/test_config.py
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("🔧 Configuration Test:")
        
        # Test OpenAI
        if settings.OPENAI_API_KEY:
            self.stdout.write(self.style.SUCCESS("✅ OpenAI API Key: Set"))
        else:
            self.stdout.write(self.style.ERROR("❌ OpenAI API Key: Missing"))
        
        # Test Cloudinary
        if settings.CLOUDINARY_CLOUD_NAME:
            self.stdout.write(self.style.SUCCESS("✅ Cloudinary Cloud Name: Set"))
        else:
            self.stdout.write(self.style.ERROR("❌ Cloudinary Cloud Name: Missing"))
        
        if settings.CLOUDINARY_API_KEY:
            self.stdout.write(self.style.SUCCESS("✅ Cloudinary API Key: Set"))
        else:
            self.stdout.write(self.style.ERROR("❌ Cloudinary API Key: Missing"))
        
        if settings.CLOUDINARY_API_SECRET:
            self.stdout.write(self.style.SUCCESS("✅ Cloudinary API Secret: Set"))
        else:
            self.stdout.write(self.style.ERROR("❌ Cloudinary API Secret: Missing"))
```

Run it:
```bash
python manage.py test_config
```

---

## 📊 **Production Deployment**

### **Railway/Render/Heroku:**
Set environment variables in your deployment platform:

```bash
# Railway CLI
railway variables set OPENAI_API_KEY=sk-your-key-here
railway variables set CLOUDINARY_CLOUD_NAME=your-cloud-name
railway variables set CLOUDINARY_API_KEY=your-api-key
railway variables set CLOUDINARY_API_SECRET=your-api-secret
```

### **Docker:**
```dockerfile
# In your Dockerfile
ENV OPENAI_API_KEY=sk-your-key-here
ENV CLOUDINARY_CLOUD_NAME=your-cloud-name
ENV CLOUDINARY_API_KEY=your-api-key
ENV CLOUDINARY_API_SECRET=your-api-secret
```

---

## ✅ **Quick Setup Checklist**

- [ ] Create `.env` file in project root
- [ ] Add OpenAI API key to `.env`
- [ ] Add Cloudinary credentials to `.env`
- [ ] Test configuration with test script
- [ ] Add `.env` to `.gitignore`
- [ ] Set environment variables in production

---

## 🎉 **Ready to Use!**

Your Django settings now load environment variables from `.env` file. You can access them anywhere in your Django app using:

```python
from django.conf import settings

# Use your API keys
openai_key = settings.OPENAI_API_KEY
cloudinary_name = settings.CLOUDINARY_CLOUD_NAME
```

**Start your server and test it! 🚀**
