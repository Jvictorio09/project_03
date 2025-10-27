# Google OAuth Setup Guide for KaTek AI

This guide will help you set up Google OAuth authentication for your KaTek AI platform with multi-tenancy support.

## 🚀 Quick Start

### 1. Google Cloud Console Setup

1. **Create/Choose Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Note your project ID

2. **Enable Google+ API**
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it
   - Also enable "Google Identity" if available

3. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" user type
   - Fill in app information:
     - App name: `KaTek AI`
     - User support email: `your-email@domain.com`
     - Developer contact: `your-email@domain.com`
   - Add scopes: `openid`, `email`, `profile`
   - Add authorized domains:
     - `localhost` (for development)
     - `yourdomain.com` (for production)
     - `staging.yourdomain.com` (for staging)

4. **Create OAuth Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Name: `KaTek Web`
   - Authorized redirect URIs:
     - `http://127.0.0.1:8000/accounts/google/login/callback/`
     - `http://localhost:8000/accounts/google/login/callback/`
     - `https://yourdomain.com/accounts/google/login/callback/`
     - `https://staging.yourdomain.com/accounts/google/login/callback/`
   - Copy Client ID and Client Secret

### 2. Django Configuration

1. **Install Dependencies**
   ```bash
   pip install django-allauth==0.57.0
   ```

2. **Environment Variables**
   Add to your `.env` file:
   ```env
   GOOGLE_CLIENT_ID=your-google-client-id-here
   GOOGLE_CLIENT_SECRET=your-google-client-secret-here
   ```

3. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

4. **Set Up Google OAuth App**
   ```bash
   python manage.py setup_google_oauth
   ```

5. **Create Superuser (if needed)**
   ```bash
   python manage.py createsuperuser
   ```

### 3. Test the Integration

1. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

2. **Test OAuth Flow**
   - Go to `http://127.0.0.1:8000/login/`
   - Click "Continue with Google"
   - Complete Google OAuth flow
   - Verify user is created and assigned to company

## 🔧 Configuration Details

### Multi-Tenancy Integration

The system automatically handles company assignment based on email domains:

- **New Users**: Creates company based on email domain
- **Existing Users**: Links to existing company if domain matches
- **Fallback**: Creates default company if no domain match

### Security Settings

- **CSRF Protection**: Configured for all environments
- **Session Security**: HttpOnly cookies with SameSite protection
- **HTTPS**: Required in production
- **Domain Validation**: Restricted to authorized domains

### Custom Adapters

The system includes custom adapters for:
- **Account Adapter**: Handles user creation and company assignment
- **Social Account Adapter**: Manages Google OAuth integration
- **Signal Handlers**: Automatic company creation and linking

## 🎨 UI Components

### Premium Google OAuth Button

The system includes a premium-styled Google OAuth button with:
- **Google Brand Colors**: Official Google color scheme
- **Smooth Animations**: Hover effects and transitions
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Responsive Design**: Works on all device sizes

### Button Locations

- **Login Page**: `/login/` - Primary OAuth option
- **Landing Page**: `/` - Signup form with OAuth
- **Consistent Styling**: Matches platform design system

## 🧪 Testing Checklist

### Development Testing

- [ ] Google OAuth button appears on login page
- [ ] Google OAuth button appears on landing page
- [ ] Clicking button redirects to Google OAuth
- [ ] Google consent screen shows correct app info
- [ ] After consent, user is redirected back to platform
- [ ] New user is created with correct email
- [ ] Company is automatically created/assigned
- [ ] User is logged in and redirected to dashboard
- [ ] Session contains company information

### Production Testing

- [ ] HTTPS is enforced
- [ ] CSRF tokens are working
- [ ] Session cookies are secure
- [ ] Domain restrictions are active
- [ ] Error handling works properly
- [ ] Mobile OAuth flow works
- [ ] Account linking works for existing users

## 🚨 Troubleshooting

### Common Issues

1. **"Redirect URI Mismatch" Error**
   - Check that all redirect URIs are added to Google Console
   - Ensure no typos in the URIs
   - Verify protocol (http vs https)

2. **"Invalid Client" Error**
   - Verify Client ID and Secret are correct
   - Check that OAuth app is enabled
   - Ensure credentials are in environment variables

3. **User Not Assigned to Company**
   - Check signal handlers are working
   - Verify company creation logic
   - Check database for company records

4. **Session Issues**
   - Verify session middleware is configured
   - Check cookie settings
   - Ensure CSRF tokens are working

### Debug Mode

Enable debug logging in settings:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'allauth': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit credentials to version control
   - Use different credentials for each environment
   - Rotate credentials regularly

2. **HTTPS in Production**
   - Always use HTTPS in production
   - Update CSRF_TRUSTED_ORIGINS for production domains
   - Set SESSION_COOKIE_SECURE = True

3. **Domain Restrictions**
   - Restrict OAuth to your domains only
   - Use email domain validation
   - Implement company invitation system

4. **Session Security**
   - Use HttpOnly cookies
   - Set appropriate SameSite policy
   - Implement session timeout

## 📚 Additional Resources

- [Django Allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.0 Security Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)

## 🎯 Next Steps

1. **Test the OAuth flow** in development
2. **Configure production domains** in Google Console
3. **Set up monitoring** for OAuth errors
4. **Implement user onboarding** flow
5. **Add additional OAuth providers** if needed

---

**Need Help?** Check the logs in `logs/app.log` for detailed error information.
