#!/usr/bin/env python
"""
Debug script to identify 500 errors when DEBUG=False
Run this to see what's causing the production error
"""

import os
import sys
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myProject.settings')
django.setup()

def test_production_settings():
    """Test production settings that might cause 500 errors"""
    print("🔍 Testing Production Settings...")
    
    # Test 1: Check if SECRET_KEY is set
    secret_key = settings.SECRET_KEY
    if secret_key == 'django-insecure-your-secret-key-here-change-in-production':
        print("❌ SECRET_KEY is still using default value!")
        return False
    else:
        print("✅ SECRET_KEY is properly set")
    
    # Test 2: Check ALLOWED_HOSTS
    allowed_hosts = settings.ALLOWED_HOSTS
    if '*' in allowed_hosts:
        print("⚠️  ALLOWED_HOSTS contains '*' - this might cause issues")
    else:
        print("✅ ALLOWED_HOSTS is properly configured")
    
    # Test 3: Check static files
    static_url = settings.STATIC_URL
    static_root = settings.STATIC_ROOT
    print(f"✅ STATIC_URL: {static_url}")
    print(f"✅ STATIC_ROOT: {static_root}")
    
    # Test 4: Check database connection
    try:
        from django.db import connection
        connection.ensure_connection()
        print("✅ Database connection works")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 5: Check if static files exist
    import os
    if os.path.exists(static_root):
        print("✅ STATIC_ROOT directory exists")
    else:
        print("❌ STATIC_ROOT directory doesn't exist - run collectstatic!")
        return False
    
    return True

def test_common_500_causes():
    """Test common causes of 500 errors"""
    print("\n🔍 Testing Common 500 Error Causes...")
    
    # Test 1: Missing environment variables
    required_env_vars = ['SECRET_KEY']
    for var in required_env_vars:
        if not os.getenv(var):
            print(f"❌ Missing environment variable: {var}")
        else:
            print(f"✅ Environment variable {var} is set")
    
    # Test 2: Check middleware
    middleware = settings.MIDDLEWARE
    if 'whitenoise.middleware.WhiteNoiseMiddleware' in middleware:
        print("✅ WhiteNoise middleware is configured")
    else:
        print("❌ WhiteNoise middleware missing!")
    
    # Test 3: Check template directories
    template_dirs = settings.TEMPLATES[0]['DIRS']
    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            print(f"✅ Template directory exists: {template_dir}")
        else:
            print(f"❌ Template directory missing: {template_dir}")
    
    # Test 4: Check static files directories
    static_dirs = settings.STATICFILES_DIRS
    for static_dir in static_dirs:
        if os.path.exists(static_dir):
            print(f"✅ Static directory exists: {static_dir}")
        else:
            print(f"❌ Static directory missing: {static_dir}")

if __name__ == "__main__":
    print("🚀 KaTek Platform - 500 Error Debugger")
    print("=" * 50)
    
    # Test production settings
    if test_production_settings():
        print("\n✅ Basic settings look good!")
    else:
        print("\n❌ Found issues with basic settings!")
    
    # Test common causes
    test_common_500_causes()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. If SECRET_KEY is default, set a proper one")
    print("2. If STATIC_ROOT missing, run: python manage.py collectstatic")
    print("3. If database issues, run: python manage.py migrate")
    print("4. Check logs/app.log for detailed error messages")
    print("5. Try DEBUG=True temporarily to see the actual error")
