
from pathlib import Path
import os
from dotenv import load_dotenv
import logging
import json

logger = logging.getLogger(__name__)

# Load environment variables from .env file
# Handle encoding issues gracefully
# Ensure .env is loaded very early so downstream settings see vars
try:
    # Load default .env from project root if present
    load_dotenv()
except Exception:
    # Fallback silently; production platforms usually inject env vars
    pass


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', '6#uds45&n3-eil26e0qv!=t4ep@u!1b-^!-n*w*+7fe*$bz!qd')

# SECURITY WARNING: don't run with debug turned on in production!
# Production settings - set DEBUG=False and proper ALLOWED_HOSTS for deployment
#DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
DEBUG = True
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,project03-production.up.railway.app').split(',')

# CSRF Trusted Origins for production deployment
CSRF_TRUSTED_ORIGINS = [
    'https://*.replit.dev',
    'https://*.replit.app',
    'https://*.railway.app',
    'https://*.railway.dev',
    'https://project03-production.up.railway.app',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',  # Add humanize for intcomma filter
    'widget_tweaks',  # Add widget_tweaks for template extras
    'cloudinary',
    'cloudinary_storage',
    
    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    # Local apps
    'myApp',  # Add your app here
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'myApp.middleware_organization.OrganizationContextMiddleware',
    'myApp.middleware_organization.OrganizationRequiredMiddleware',
    'myApp.middleware_organization.OrganizationPermissionsMiddleware',
    'myApp.middleware.CompanyContextMiddleware',  # Legacy
    'myApp.middleware.RequestLoggingMiddleware',
    'myApp.middleware.LoginRequiredMiddleware',
    'myApp.middleware.WizardGatingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'myApp.context_processors.feature_flags',
                'myApp.context_processors.company_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'myProject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Use PostgreSQL in production, SQLite in development
if os.getenv('DATABASE_URL'):
    # Production: PostgreSQL with pgvector
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
    }
else:
    # Development: SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'

# Static files configuration
if DEBUG:
    # Development: serve from static/ directory
    STATICFILES_DIRS = [BASE_DIR / 'static']
    STATIC_ROOT = None
else:
    # Production: serve from staticfiles/ directory (after collectstatic)
    STATICFILES_DIRS = []
    STATIC_ROOT = BASE_DIR / 'staticfiles'

# Production static files serving
if not DEBUG:
    # In production, serve static files with WhiteNoise
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    # In development, use default storage
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# WhiteNoise middleware for serving static files in production
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')  # right after SecurityMiddleware

# Storage configuration
STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage' if not DEBUG else 'django.contrib.staticfiles.storage.StaticFilesStorage',
    }
}

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
MEDIA_URL = "/media/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# API Keys and External Services Configuration
# ============================================================================

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Cloudinary Configuration
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
}

# Email Configuration (Resend)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'resend'
EMAIL_HOST_PASSWORD = os.getenv('RESEND_API_KEY')
DEFAULT_FROM_EMAIL = os.getenv('RESEND_FROM', 'noreply@katek.ai')
SERVER_EMAIL = os.getenv('RESEND_FROM', 'noreply@katek.ai')

# Authentication settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard'
LOGOUT_REDIRECT_URL = '/'

# Webhook settings
WEBHOOK_SIGNING_SECRET = os.getenv('WEBHOOK_SIGNING_SECRET', 'your-webhook-secret-key')

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# LemonSqueezy Configuration (alternative to Stripe)
LEMONSQUEEZY_API_KEY = os.getenv('LEMONSQUEEZY_API_KEY', '')
LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv('LEMONSQUEEZY_WEBHOOK_SECRET', '')

# Email Provider Configuration
POSTMARK_API_TOKEN = os.getenv('POSTMARK_API_TOKEN', '')
POSTMARK_FROM_EMAIL = os.getenv('POSTMARK_FROM_EMAIL', 'noreply@katek.ai')

# AWS SES Configuration (alternative to Postmark)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_SES_REGION = os.getenv('AWS_SES_REGION', 'us-east-1')

# Vector Database Configuration
VECTOR_DIMENSIONS = 1536  # OpenAI text-embedding-3-small
EMBEDDING_MODEL = 'text-embedding-3-small'

# Social Media Integration
FACEBOOK_VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN', 'your-facebook-verify-token')
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '')

# Celery Configuration (for background tasks) - DEPRECATED: Using n8n instead
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# n8n Integration Configuration
N8N_TOKEN = os.getenv('N8N_TOKEN', '')
N8N_HMAC_SECRET = os.getenv('N8N_HMAC_SECRET', '')
USE_N8N_ORCHESTRATION = os.getenv('USE_N8N_ORCHESTRATION', 'False').lower() == 'true'
N8N_QUEUE_WEBHOOK_URL = os.getenv('N8N_QUEUE_WEBHOOK_URL', '')

# Postmark Inbound Email Configuration
POSTMARK_INBOUND_SECRET = os.getenv('POSTMARK_INBOUND_SECRET', '')

# Feature Flags
FEATURE_DASHBOARD_REAL_DATA = os.getenv('FEATURE_DASHBOARD_REAL_DATA', 'True').lower() == 'true'

# Environment settings
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Logging configuration
from pathlib import Path

# Ensure logs directory exists
logs_dir = BASE_DIR / 'logs'
logs_dir.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'myApp.utils.logging_config.StructuredFormatter',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(logs_dir / 'app.log'),
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 5,
            'formatter': 'standard',
        },
    },
    'loggers': {
        'myApp': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'request': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# Django Allauth Configuration
# ============================================================================

# Site ID (required for allauth)
SITE_ID = 1

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGIN_REDIRECT_URL = '/dashboard'
ACCOUNT_SIGNUP_REDIRECT_URL = '/setup'

# Social account settings
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'  # Google handles email verification
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_AUTO_SIGNUP = True

# Google OAuth settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# Security settings for OAuth
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://project03-production.up.railway.app',
    'https://yourdomain.com',
    'https://staging.yourdomain.com',
]

# Session settings
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Security settings for production
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'

# Railway proxy settings - fixes HTTPS redirect_uri_mismatch
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Environment variables for Google OAuth
# Try environment variables first; if not present, fall back to client_secret_*.json
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    # Attempt to load from Google OAuth client JSON in project root
    try:
        for filename in os.listdir(BASE_DIR):
            if str(filename).startswith('client_secret_') and str(filename).endswith('.json'):
                json_path = Path(BASE_DIR) / filename
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Support both "web" and top-level formats
                client_data = data.get('web', data)
                GOOGLE_CLIENT_ID = GOOGLE_CLIENT_ID or client_data.get('client_id', '')
                GOOGLE_CLIENT_SECRET = GOOGLE_CLIENT_SECRET or client_data.get('client_secret', '')
                break
    except Exception as e:
        # Do not crash settings; logging occurs later when used
        logger.warning("Failed to read Google OAuth client JSON: %s", e)

# Custom allauth adapters
ACCOUNT_ADAPTER = 'myApp.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'myApp.adapters.CustomSocialAccountAdapter'