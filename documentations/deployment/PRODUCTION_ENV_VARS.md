# KaTek Real Estate Platform - Production Environment Variables
# Copy this to your deployment platform (Railway, Heroku, etc.)

# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ALLOWED_HOSTS=your-domain.com,your-railway-app.railway.app

# Database (use PostgreSQL for production)
DATABASE_URL=postgresql://user:password@host:port/database

# Cloudinary (for media files)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# n8n Webhook URLs
N8N_BASE_URL=https://your-n8n-instance.com
N8N_WEBHOOK_SECRET=your-webhook-secret

# Email Settings (for production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

# Security
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
