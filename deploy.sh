#!/bin/bash

# KaTek Real Estate Platform - Production Deployment Script
echo "🚀 Starting KaTek Platform Deployment..."

# Set production environment
export DEBUG=False
export ALLOWED_HOSTS="your-domain.com,your-railway-app.railway.app"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Collect static files for production
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if needed (optional)
echo "👤 Creating superuser (optional)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@katek.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Run system checks
echo "🔍 Running system checks..."
python manage.py check --deploy

echo "✅ Deployment completed successfully!"
echo "🌐 Your app should now be running with proper static files!"
