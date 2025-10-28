# 🔑 API Keys Setup Guide

## 🚨 CRITICAL: Required API Keys

Your application is missing API keys. Follow these steps to configure them:

---

## ⚡ Quick Fix (5 minutes)

### 1. **OpenAI API Key** (Required for AI features)

**Get your key:**
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

**Add to .env:**
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

💰 **Cost**: Pay-as-you-go (~$0.002 per chat message)

---

### 2. **Cloudinary API Keys** (Required for image uploads)

**Get your keys:**
1. Go to https://cloudinary.com/users/register/free
2. Sign up (free tier available)
3. Go to Dashboard: https://console.cloudinary.com/
4. Copy your credentials:
   - Cloud Name
   - API Key
   - API Secret

**Add to .env:**
```bash
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=abcdefghijklmnopqrstuvwxyz
```

💰 **Cost**: Free tier (25 credits/month, ~25,000 images)

---

## 📝 Step-by-Step Instructions

### Step 1: Edit .env file

Open `.env` file in the project root and replace the placeholder values:

```bash
# BEFORE (won't work):
OPENAI_API_KEY=your-openai-api-key-here
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name

# AFTER (with real keys):
OPENAI_API_KEY=sk-proj-abc123xyz789...
CLOUDINARY_CLOUD_NAME=myapp-cloud
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=abcXYZ123def456
```

### Step 2: Restart Django server

```bash
# Stop server (Ctrl+C)
# Then restart:
python manage.py runserver
```

### Step 3: Test

1. Go to Upload a Listing → AI Prompt
2. Try uploading an image
3. Provide property description
4. Should work without errors ✅

---

## 🔍 Verify Configuration

Run this to check if keys are loaded:

```bash
python manage.py shell
```

Then in the shell:
```python
from django.conf import settings
print(f"OpenAI Key: {settings.OPENAI_API_KEY[:20]}..." if settings.OPENAI_API_KEY else "NOT SET")
print(f"Cloudinary Name: {settings.CLOUDINARY_STORAGE.get('CLOUD_NAME')}")
print(f"Cloudinary Key: {settings.CLOUDINARY_STORAGE.get('API_KEY')[:10]}..." if settings.CLOUDINARY_STORAGE.get('API_KEY') else "NOT SET")
```

Expected output:
```
OpenAI Key: sk-proj-abc123xyz789...
Cloudinary Name: myapp-cloud
Cloudinary Key: 1234567890...
```

---

## ❌ Current Errors (Will be fixed after setup)

### Error 1: Cloudinary
```
❌ Cloudinary upload failed: Must supply api_key
Cloud Name: None
API Key: NOT SET
```
**Fix**: Add Cloudinary credentials to .env

### Error 2: OpenAI
```
OpenAI error: Invalid URL 'None/chat/completions': No scheme supplied
```
**Fix**: Add OpenAI API key to .env

---

## 🆓 Free Alternatives (If you don't want to pay)

### Option 1: Disable AI Features (Use Manual Form Only)
- Use Manual Form for property uploads
- Skip AI validation
- Images stored locally (no Cloudinary needed)

### Option 2: Mock/Development Mode
Create a `.env` with dummy values for testing:
```bash
OPENAI_API_KEY=test-key-development-mode
CLOUDINARY_CLOUD_NAME=test
CLOUDINARY_API_KEY=test
CLOUDINARY_API_SECRET=test
```

Then modify the code to skip actual API calls in development.

---

## 📞 Need Help?

1. **OpenAI Issues**: https://help.openai.com/
2. **Cloudinary Issues**: https://support.cloudinary.com/
3. **Check logs**: Look for specific error messages in terminal

---

## ✅ Checklist

- [ ] Created OpenAI account and got API key
- [ ] Created Cloudinary account and got credentials
- [ ] Updated `.env` file with real keys
- [ ] Restarted Django server
- [ ] Tested image upload (no errors)
- [ ] Tested AI features (no errors)

Once all checked, your app will work perfectly! 🎉

