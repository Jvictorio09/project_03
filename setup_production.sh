#!/bin/bash

# KaTek Platform - Production Environment Setup
echo "🚀 Setting up KaTek Platform for Production..."

# Generate a secure secret key
echo "🔐 Generating secure SECRET_KEY..."
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# Set production environment variables
echo "⚙️ Setting production environment variables..."
export SECRET_KEY="$SECRET_KEY"
export DEBUG=False
export ALLOWED_HOSTS="your-domain.com,your-app.railway.app"
export SESSION_COOKIE_SECURE=True
export CSRF_COOKIE_SECURE=True
export SECURE_SSL_REDIRECT=True
export SECURE_HSTS_SECONDS=31536000

# Show the generated secret key
echo "✅ Generated SECRET_KEY: $SECRET_KEY"
echo ""
echo "📋 Add these environment variables to your deployment platform:"
echo "SECRET_KEY=$SECRET_KEY"
echo "DEBUG=False"
echo "ALLOWED_HOSTS=your-domain.com,your-app.railway.app"
echo "SESSION_COOKIE_SECURE=True"
echo "CSRF_COOKIE_SECURE=True"
echo "SECURE_SSL_REDIRECT=True"
echo "SECURE_HSTS_SECONDS=31536000"
echo ""

# Run Django checks
echo "🔍 Running Django system checks..."
python manage.py check --deploy

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

echo "✅ Production setup complete!"
echo "🎯 Your app should now work with DEBUG=False!"
